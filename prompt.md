請幫我將以下的流程撰寫為 python script:

1. 在 input 指定本地若干個檔案（通常是圖片，但不驗證）
2. 清理遠端的輸入＆輸出資料夾（將執行的指令含 SSH 完整印出來確認，^C就取消）
3. 使用 scp 將檔案傳至遠端的「輸入資料夾」
4. 使用 ssh 遠端操作 magick 指令，逐一將輸入資料夾內的圖片都使用**指令A**轉換
5. 使用 ssh 遠端操作 magick 指令，將所有輸入資料夾中的圖片使用**指令B**整合並輸出為 PDF
6. 使用 scp 將圖片傳回

注意，ssh、scp 直接操作指令，而輸入、輸出資料夾、remote host 則由一個與 script 同位置的 env.json 表示：

```json
{
    "host": "rpi",
    "input": "/home/bladeisoe/app/image-to-pdf/src/",
    "output": "/home/bladeisoe/app/image-to-pdf/dist/"
}
```

指令A：

`magick (...)/src/(...).jpg -define jpeg:extent=400kb -resize 2480x3508 -background white -gravity center -extent 2480x3508 (...)/dist/img/(...).jpg`

指令B：

`magick [(...)/dist/img/(...).jpg]* (...)/dist/export.pdf`
