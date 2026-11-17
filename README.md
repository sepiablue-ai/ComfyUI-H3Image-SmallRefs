# ComfyUI-H3Image-SmallRefs

[日本語](#日本語) | [English](#english)

---

## 日本語

MiniMax-H3-Image 用の非公式 ComfyUI カスタムノードです。1枚目の参照画像（編集する人物など）は標準ノードと同じサイズで処理し、2枚目以降の参照画像（小物）を小さいサイズ（既定は長辺512 px）で処理します。

### なぜ必要か

標準の `MiniMax H3 Image Conditioning` は、すべての参照画像をテキストエンコーダ用に短辺1024 px、VAE用に短辺1024〜2048 pxへ調整します。短辺が1024 pxより小さい画像は**拡大**されます。そのため、`ImageScaleToMaxDimension` などで先に縮小しても、標準ノードの中で元の大きさに戻り、速くなりません。参照サイズを変える入力欄もありません。

確認した例（4枚参照、どれも ComfyUI 起動直後の1回目）:

| 条件 | 時間 |
|---|---|
| 標準ノード、元の画像 | 91.02秒 |
| 標準ノード、小物3枚を先に長辺512 pxへ縮小 | 87.13秒 |
| このノード（`ref_long_edge` = 512） | 50.04秒 |

### 実測（RTX 4070 12GB、H3 Image W4A8、出力2496×1664、6ステップ）

| 参照枚数 | 標準ノード | このノード（長辺512 px） |
|---|---|---|
| 4 | 91.02秒 | 41.76秒 |
| 8 | 186.66秒 | 55.78秒 |
| 12 | 325.88秒 | 68.00秒 |
| 16 | 先行試行でメモリ逼迫のため中断 | 81.70秒 |
| 20 | 先行試行で実行できず | 96.30秒 |

- 各条件1回の計測です。上の表の「このノード」の4枚は、モデルを読み込み済みの状態で測りました。
- 4・8・12枚では、確認できた小物の数は標準ノードと同じでした。ただし、腕時計の文字盤の色やイヤリングの形など、細かい部分が変わることがあります。
- **注意**: 小物を縮小する使い方は公式の想定外で、品質は公式に保証されていません。公式の参照上限は16枚です。

### 導入

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/sepiablue-ai/ComfyUI-H3Image-SmallRefs
```

1. 上のコマンドで `custom_nodes` に入れます。追加の依存パッケージはありません。ComfyUI Manager や Comfy Registry には登録していないので、Manager からは入れられません。
2. **ComfyUI を再起動し、ブラウザのページも再読み込み**してください。再起動前に開いたワークフローでは、このノードは「不足しているノード」として扱われ、線が外れます。
3. ノード一覧の `model/conditioning/minimax` に `H3 Image Conditioning (small refs)` が追加されます。

### 使い方

標準の `MiniMax H3 Image Conditioning` の代わりに使います。つなぎ方は標準ノードと同じです。

| 入力 | 内容 |
|---|---|
| `clip` | MiniMax-H3-Image のテキストエンコーダ（`CLIPLoader` の type は `minimax`） |
| `vae` | MiniMax-H3-Image の VAE |
| `prompt` | プロンプト。画像は `<Picture 1>`、`<Picture 2>` … で指定します |
| `width` / `height` | 出力サイズ（32 px単位）。0 のときは1枚目の画像の VAE 用サイズを使います。画像がないときは 2048×2048 です |
| `ref_long_edge` | 2枚目以降の画像の長辺（px、32〜2048、既定512）。下の「画像の扱い」を参照してください |
| `images` | 参照画像。1つつなぐと次の入力欄が増えます |

出力は標準ノードと同じで、`positive`（`KSampler` の positive と、`ConditioningZeroOut` 経由で negative へ）と `LATENT`（`KSampler` の latent_image へ）です。

#### 画像の順番

- **1つ目の入力欄につないだ画像が1枚目**で、編集する画像（人物など）として扱います。画面では入力欄の名前が `image_0` から始まるので、`image_0` が1枚目です。API から使う場合は `image_1` 始まりでも構いません。名前の番号順に並べ、先頭を1枚目とします。
- プロンプトの `<Picture 1>` は1枚目、`<Picture 2>` は2枚目…に対応します。画面の入力欄の名前（`image_0`、`image_1` …）とは番号が1つずれるので注意してください。

#### 画像の扱い

- **1枚目**: 標準ノードと同じです。テキストエンコーダ用は短辺1024 px、VAE用は短辺1024〜2048 pxに調整します。
- **2枚目以降**: テキストエンコーダ用・VAE用とも、縦横比を保って長辺を `ref_long_edge` にそろえます。
  - 元の画像が `ref_long_edge` より大きければ縮小し、**小さければ拡大**します。
  - 短辺は32 px単位に丸めます。例（`ref_long_edge` = 512）: 1312×1199 → 512×480、1536×1024 → 512×352。
- サイズの変更には lanczos を使います。アルファチャンネルは使わず、バッチで複数枚つないだ場合は1枚目だけを使います。
- **確認したのは `ref_long_edge` = 512 だけです。** ほかの値での速さや再現度は確かめていません。

### ワークフローの例

上の実測で使った4枚参照の条件です。

- `workflows/example_4refs.json`: ComfyUI の画面にドラッグ＆ドロップして使います。
- `workflows/example_4refs.api.json`: API（`/prompt`）から実行する用です。画面に読み込むと画像の接続が外れるので、画面では使わないでください。

例で使っているファイル（お使いの環境に合わせて差し替えてください）:

- 拡散モデル: `minimax_h3_image_pruned_w4a8.safetensors`
- テキストエンコーダ: `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`
- VAE: `minimax_h3_image_vae_fp16.safetensors`
- 画像: `ref_01.webp`（人物）、`ref_02.png`〜`ref_04.png`（小物）。画像は同梱していません。`ComfyUI/input` に置くか、`Load Image` からアップロードしてください。
- サンプラー: `KSampler`、シード261113（固定）、6ステップ、cfg 1、euler、simple。negative は `ConditioningZeroOut` です。

### 動作確認

- ComfyUI 0.45.0、RTX 4070 12GB。
- `workflows/example_4refs.json` を画面から読み込んで実行し、上の表の4枚の結果と画素まで一致することを確認しました。
- 参照画像の受け渡しは ComfyUI 内部の `minimax_refs` という形式に依存しています。ComfyUI 側の仕様が変わると動かなくなる可能性があります。

### ライセンス

GPL-3.0（ComfyUI 本体に合わせています）

---

## English

An unofficial ComfyUI custom node for MiniMax-H3-Image. The first reference picture (the one to edit, such as a person) is processed at the same size as the stock node, and the second and later reference pictures (props) are processed at a smaller size (512 px long edge by default).

### Why

The stock `MiniMax H3 Image Conditioning` node scales every reference picture to a 1024 px short edge for the text encoder and to a 1024-2048 px short edge for the VAE. Pictures with a short edge below 1024 px are **upscaled**. Shrinking them beforehand with `ImageScaleToMaxDimension` or similar does not help, because the stock node scales them back up. The stock node has no input to change the reference size.

Example (4 references, each the first run after starting ComfyUI):

| Condition | Time |
|---|---|
| Stock node, original pictures | 91.02 s |
| Stock node, 3 props shrunk to a 512 px long edge beforehand | 87.13 s |
| This node (`ref_long_edge` = 512) | 50.04 s |

### Measurements (RTX 4070 12GB, H3 Image W4A8, 2496×1664 output, 6 steps)

| References | Stock node | This node (512 px long edge) |
|---|---|---|
| 4 | 91.02 s | 41.76 s |
| 8 | 186.66 s | 55.78 s |
| 12 | 325.88 s | 68.00 s |
| 16 | Stopped in an earlier trial (memory pressure) | 81.70 s |
| 20 | Could not run in an earlier trial | 96.30 s |

- One run per condition. The 4-reference run of this node in the table was measured with the models already loaded.
- With 4, 8 and 12 references, the number of props that appeared was the same as with the stock node. Small details can change, such as the color of a watch face or the shape of earrings.
- **Note**: Shrinking props is not an officially intended use, and quality is not guaranteed by the model authors. The official reference limit is 16 pictures.

### Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/sepiablue-ai/ComfyUI-H3Image-SmallRefs
```

1. Clone the repository into `custom_nodes` with the command above. There are no extra dependencies. The node is not registered in ComfyUI Manager or the Comfy Registry, so it cannot be installed from the Manager.
2. **Restart ComfyUI and reload the browser page.** A workflow opened before the restart treats this node as missing, and its links are dropped.
3. `H3 Image Conditioning (small refs)` appears under `model/conditioning/minimax`.

### Usage

Use it in place of the stock `MiniMax H3 Image Conditioning` node. The connections are the same as for the stock node.

| Input | Description |
|---|---|
| `clip` | The MiniMax-H3-Image text encoder (`CLIPLoader` with type `minimax`) |
| `vae` | The MiniMax-H3-Image VAE |
| `prompt` | The prompt. Refer to the pictures as `<Picture 1>`, `<Picture 2>`, ... |
| `width` / `height` | Output size (multiples of 32). 0 uses the VAE size of the first picture, or 2048×2048 without pictures |
| `ref_long_edge` | Long edge in px for the second and later pictures (32-2048, default 512). See "How pictures are scaled" below |
| `images` | Reference pictures. A new slot appears each time one is connected |

The outputs are the same as the stock node: `positive` (to `KSampler` positive, and through `ConditioningZeroOut` to negative) and `LATENT` (to `KSampler` latent_image).

#### Picture order

- **The picture connected to the first slot is the first picture**, and it is treated as the picture to edit (such as a person). In the UI the slots are named from `image_0`, so `image_0` is the first picture. API prompts may also number them from `image_1`. Slots are sorted by their number and the first one is the first picture.
- `<Picture 1>` in the prompt is the first picture, `<Picture 2>` the second, and so on. This is one higher than the slot names in the UI (`image_0`, `image_1`, ...).

#### How pictures are scaled

- **First picture**: Same as the stock node. A 1024 px short edge for the text encoder and a 1024-2048 px short edge for the VAE.
- **Second and later pictures**: For both the text encoder and the VAE, the long edge is set to `ref_long_edge` while keeping the aspect ratio.
  - Pictures larger than `ref_long_edge` are shrunk, and **smaller ones are upscaled**.
  - The short edge is rounded to a multiple of 32 px. Examples (`ref_long_edge` = 512): 1312×1199 → 512×480, 1536×1024 → 512×352.
- Scaling uses lanczos. The alpha channel is ignored, and only the first image of a batch is used.
- **Only `ref_long_edge` = 512 has been tested.** Speed and fidelity at other values have not been checked.

### Example workflows

The 4-reference condition from the measurements above.

- `workflows/example_4refs.json`: Drag and drop it onto the ComfyUI UI.
- `workflows/example_4refs.api.json`: For running through the API (`/prompt`). Loading it in the UI drops the picture links, so do not use it in the UI.

Files used in the example (replace them with your own):

- Diffusion model: `minimax_h3_image_pruned_w4a8.safetensors`
- Text encoder: `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`
- VAE: `minimax_h3_image_vae_fp16.safetensors`
- Pictures: `ref_01.webp` (person), `ref_02.png` to `ref_04.png` (props). The pictures are not included. Put them in `ComfyUI/input` or upload them through `Load Image`.
- Sampler: `KSampler`, seed 261113 (fixed), 6 steps, cfg 1, euler, simple. The negative is `ConditioningZeroOut`.

### Testing

- ComfyUI 0.45.0, RTX 4070 12GB.
- `workflows/example_4refs.json` was loaded and run from the UI, and the output matched the 4-reference result in the table above pixel for pixel.
- The references are passed through ComfyUI's internal `minimax_refs` format. The node may stop working if ComfyUI changes it.

### License

GPL-3.0 (same as ComfyUI)
