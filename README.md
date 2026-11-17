# ComfyUI-H3Image-SmallRefs

MiniMax-H3-Image の参照画像のうち、**編集対象（1枚目につないだ画像）以外の小物画像だけを小さく（既定は長辺512 px）して**処理する ComfyUI 用の非公式カスタムノードです。

An unofficial ComfyUI node for MiniMax-H3-Image: keeps the first picture at the stock reference size and scales the other references to a smaller long edge (512 px by default).

## なぜ必要か

標準の `MiniMax H3 Image Conditioning` は、すべての参照画像をテキストエンコーダ用に短辺1024 px、VAE用に短辺1024〜2048 pxへ調整します。小さい画像も1024 pxへ**拡大**されるため、`ImageScaleToMaxDimension` などで先に縮小しても効果がありません。参照サイズを変える入力もありません。

このノードは、1枚目（人物など編集対象）は標準と同じサイズのまま、2枚目以降を `ref_long_edge` の長辺（短辺は元の比率のまま32 px単位）に縮小し、テキストエンコーダとVAEの両方へ渡します。

## 実測（RTX 4070 12GB、H3 Image W4A8、出力2496×1664、6ステップ）

| 参照枚数 | 標準ノード | このノード（長辺512 px） |
|---|---|---|
| 4 | 91.02秒 | 41.76秒 |
| 8 | 186.66秒 | 55.78秒 |
| 12 | 325.88秒 | 68.00秒 |
| 16 | 未実行 | 81.70秒 |
| 20 | 未実行 | 96.30秒 |

各条件1回の計測です。4・8・12枚では、確認できた小物の数は標準ノードと同じでした。一方で、腕時計の文字盤の色やイヤリングの形など、細かい部分は崩れることがあります。

**注意**: 小物を縮小する使い方は公式の想定外です。品質は公式に保証されていません。公式の参照上限は16枚です。

## 導入

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/sepiablue-ai/ComfyUI-H3Image-SmallRefs
```

ComfyUI を再起動すると `H3 Image Conditioning (small refs)` が追加されます（カテゴリ `model/conditioning/minimax`）。追加の依存パッケージはありません。

## 使い方

標準の `MiniMax H3 Image Conditioning` と差し替えて使います。入力は標準ノードと同じで、次の1つが増えています。

- `ref_long_edge`（既定512）: 2枚目以降の長辺（px）。1枚目には適用されません。画面では入力欄が image_0 から始まるので、image_0 が1枚目です。

ワークフローの例（上の実測で使った4枚参照の条件）:

- `workflows/example_4refs.json`: ComfyUI の画面にドラッグ＆ドロップして使うワークフローです。
- `workflows/example_4refs.api.json`: API（`/prompt`）から実行する用です。画面に読み込むと画像の接続が外れるので、画面では使わないでください。

画像ファイル（`ref_01.webp` など）は含めていないので、ご自分の画像に差し替えてください。1枚目（`image_0`）に編集する人物、2枚目以降に小物をつなぎます。

## 動作確認

- ComfyUI 0.45.0
- `workflows/example_4refs.json` を画面から読み込んで実行し、上の表の4枚の結果と画素まで一致することを確認しています。
- API 形式（入力名 `image_1` 始まり）と画面（入力名 `image_0` 始まり）のどちらでも、ノード内の縮小・エンコード処理が同じになることをモックで確認しています。
- 参照の受け渡しは ComfyUI 内部の `minimax_refs` という形式に依存しています。ComfyUI 側の仕様が変わると動かなくなる可能性があります。

## ライセンス

GPL-3.0（ComfyUI 本体に合わせています）
