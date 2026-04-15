import json
import subprocess
import os
import sys

def run_command(cmd, shell=False):
    """執行指令並確認回傳碼"""
    try:
        subprocess.run(cmd, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[錯誤] 指令執行失敗: {e}")
        sys.exit(1)

def main():
    # 0. 讀取設定檔
    config_path = os.path.join(os.path.dirname(__file__), 'env.json')
    try:
        with open(config_path, 'r') as f:
            env = json.load(f)
    except FileNotFoundError:
        print(f"錯誤：找不到設定檔 {config_path}")
        return

    host = env['host']
    remote_src = env['input'].rstrip('/')
    remote_dist = env['output'].rstrip('/')
    # 假設指令 A 的子目錄為 dist/img
    remote_dist_img = f"{remote_dist}/img"

    # 1. 指定本地檔案與 resize 選項
    if len(sys.argv) < 3:
        print("用法: python convert.py <resize_option> <file1> <file2> ...")
        print("選項 (resize_option): a4-vertical, a4-horizontal, 16-9")
        return
    
    resize_option = sys.argv[1]
    resize_map = {
        "a4-vertical": "2480x3508",
        "a4-horizontal": "3508x2480",
        "16-9": "3840x2160"
    }
    if resize_option not in resize_map:
        print(f"無效的選項 '{resize_option}'，請使用: a4-vertical, a4-horizontal, 16-9")
        return
    
    resize_dim = resize_map[resize_option]
    local_files = sys.argv[2:]

    # 2. 清理遠端資料夾 (含確認機制)
    # 建立目錄確保路徑存在，並清空內容
    clean_cmd = f"ssh {host} 'mkdir -p {remote_src} {remote_dist_img} && rm -rf {remote_src}/* {remote_dist_img}/* {remote_dist}/*.pdf'"
    
    print("\n--- 準備執行遠端清理指令 ---")
    print(f"指令: {clean_cmd}")
    print("---------------------------")
    try:
        input("確認執行請按 [Enter]，取消請按 [Ctrl+C]...")
    except KeyboardInterrupt:
        print("\n已取消執行。")
        return

    run_command(clean_cmd, shell=True)

    # 3. 使用 scp 將檔案傳至遠端「輸入資料夾」
    print(f"\n[Step 3] 上傳檔案至 {host}:{remote_src}...")
    scp_cmd = ["scp"] + local_files + [f"{host}:{remote_src}/"]
    run_command(scp_cmd)

    # 4. 指令 A: 逐一轉換
    # 在遠端使用 shell loop 處理
    print(f"\n[Step 4] 執行指令 A (圖片轉換為 {resize_dim})...")
    cmd_a = (
        f"ssh {host} \"for f in {remote_src}/*; do "
        f"filename=\\$(basename \\\"\\$f\\\"); "
        f"magick \\\"\\$f\\\" -define jpeg:extent=400kb -resize {resize_dim} "
        f"-background white -gravity center -extent {resize_dim} "
        f"\\\"{remote_dist_img}/\\${{filename}}\\\"; "
        f"done\""
    )
    run_command(cmd_a, shell=True)

    # 5. 指令 B: 整合為 PDF
    print(f"\n[Step 5] 執行指令 B (整合 PDF)...")
    cmd_b = f"ssh {host} 'magick {remote_dist_img}/* {remote_dist}/export.pdf'"
    run_command(cmd_b, shell=True)

    # 6. 使用 scp 將檔案傳回
    print(f"\n[Step 6] 下載結果...")
    local_download_path = "./output_result.pdf"
    download_cmd = ["scp", f"{host}:{remote_dist}/export.pdf", local_download_path]
    run_command(download_cmd)

    print(f"\n完成！檔案已儲存至: {local_download_path}")

if __name__ == "__main__":
    main()
