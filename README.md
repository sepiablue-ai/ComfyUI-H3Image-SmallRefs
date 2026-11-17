# ComfyUI-H3Image-SmallRefs

MiniMax-H3-Image の参照画像のうち、**編集対象（image_1）以外の小物画像だけを小さく（既定は長辺512 px）して**処理する ComfyUI 用の非公式カスタムノードです。

An unofficial ComfyUI node for MiniMax-H3-Image: keeps `image_1` at the stock reference size and scales the other references to a smaller long edge (512 px by default).

## なぜ必要か

標準の `MiniMax H3 Image Conditioning` は、すべての参照画像をテキストエンコーダ用に短辺1024 px、VAE用に短辺1024〜2048 pxへ調整します。小さい画像も1024 pxへ**拡大**されるため、`ImageScaleToMaxDimension` などで先に縮小しても効果がありません。参照サイズを変える入力もありません。

このノードは、image_1 は標準と同じサイズのまま、image_2 以降を `ref_long_edge` の長辺（短辺は元の比率のまま32 px単位）に縮小し、テキストエンコーダとVAEの両方へ渡します。

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

- `ref_long_edge`（既定512）: image_2 以降の長辺（px）。image_1 には適用されません。

`workflows/example_4refs.api.json` は、上の実測で使った4枚参照の API 形式ワークフローです。画像ファイル（`ref_01.webp` など）は含めていないので、ご自分の画像に差し替えてください。

## 動作確認

- ComfyUI 0.45.0
- ノード内の縮小・エンコード処理は、上の実測に使った検証用ノードと同一の入力テンソルになることをモックで確認しています。
- 参照の受け渡しは ComfyUI 内部の `minimax_refs` という形式に依存しています。ComfyUI 側の仕様が変わると動かなくなる可能性があります。

## ライセンス

GPL-3.0（ComfyUI 本体に合わせています）
