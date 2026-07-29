# Overleaf 上传与编译指南（JISE）

## 1. 上传前你需要知道的事

这个目录已经按 JISE 官网提供的官方 LaTeX 模板整理。当前阶段只用于在线
编辑、编译和校样，不代表已经投稿。请不要在 Overleaf 中填写虚假的作者、基金、
伦理或数据开放信息。

## 2. 最简单的上传方法

1. 打开 <https://www.overleaf.com/> 并登录你自己的账号。
2. 点击左侧或主页上的 **New Project**。
3. 选择 **Upload Project**。
4. 上传本目录对应的 ZIP 文件：`JISE_OVERLEAF_LATEX_20260729.zip`。
5. Overleaf 解压后，应能在左侧看到 `main.tex`、`frontmatter.tex`、
   `references.bib`、`JISE.sty`、`JISEbib.bst`、`latexmkrc` 和 `sections/`。

不要只上传 `main.tex`。官方样式、参考文献和章节文件缺失都会导致编译失败。

## 3. 设置主文件和编译器

1. 打开 Overleaf 左上角 **Menu**。
2. 在 **Main document** 中选择 `main.tex`。如果系统已经自动选择它，无需更改。
3. 在 **Compiler** 中选择 **pdfLaTeX**。
4. TeX Live 版本可先使用 Overleaf 当前默认版本。
5. 关闭菜单，点击绿色 **Recompile**。

第一次编译参考文献可能需要多轮；Overleaf 通常会自动运行 BibTeX 并重复编译。
如果引用暂时显示为问号，再点一次 **Recompile**。若仍未恢复，使用
**Recompile from scratch**。

## 4. 先处理作者信息

打开 `frontmatter.tex`，逐项替换：

- `[AUTHOR INPUT: AUTHOR 1 FULL NAME]`；
- `[AUTHOR INPUT: AUTHOR 2 FULL NAME]`；
- 两个单位和地址；
- 作者邮箱；
- `SHORT AUTHOR LIST`（页眉短作者名，例如 `Y. Zhang and H. Li`）。
- `main.tex` 中的通讯作者姓名、完整邮寄地址和邮箱。

官方模板用作者名右上角的 `+` 表示通讯作者。当前示例把 `+` 放在作者 2 后面；
请根据真实情况移动，不能默认作者 2 是通讯作者。通讯作者完整邮寄地址和邮箱也要
与投稿系统一致。

如作者不止两位，可复制作者和单位写法；如只有一位，删除第二位作者及第二单位，
不要保留空占位符。

## 5. 再处理声明

打开 `sections/10_disclosures.tex`，解决所有粗体
`[AUTHOR INPUT: ...]` 标记：

1. 非 AI 致谢（没有则删掉整句）；
2. 基金及项目号；
3. 利益冲突；
4. 数据可用性；
5. 代码可用性；
6. 机构确认的伦理表述；
7. 真实 CRediT 作者分工。

这些内容应以 Markdown 投稿包中的
`04_DECLARATIONS_AND_AI_DISCLOSURE.md` 为选择依据。AI 使用披露已经写入 LaTeX，
其中新增了本轮 LaTeX 模板转换用途；不要把它简化成“AI 仅用于润色”。

## 6. 检查正文和参考文献

- 正文位于 `sections/`，修改后不要改变锁定的实验数字。
- `references.bib` 含正文实际引用的 17 条来源。
- JISE 使用按正文首次出现顺序编号的方括号引用；`JISEbib.bst` 会生成该格式。
- 不要手工把 `\cite{...}` 改成固定的 `[1]`，否则增删文献时编号会错乱。

## 7. 编译成功后检查什么

在右侧 PDF 中逐页检查：

1. 标题、作者、单位和通讯作者是否正确；
2. 摘要与六个关键词是否完整；
3. 五张表是否超出页面或出现断行错误；
4. 所有引用是否显示为数字而不是 `?`；
5. 参考文献是否恰好 17 条且按首次引用顺序排列；
6. 是否仍出现 `[AUTHOR INPUT: ...]`；
7. 页眉中的 `XX, XXXX-XXXX (2024)` 和 DOI 占位内容是否属于官方样式文件。

最后一项来自 JISE 2016 版官方 `JISE.sty`，作者不应自行编造卷期、页码或 DOI。
正式上传前应询问编辑部是否接受该模板当前显示方式，或是否由编辑部后处理。

## 8. 页数与投稿红线

JISE 官网同时出现“常规稿 25 页以内”和“12 页模板界线/超页费”的表述。本项目
仍以不超过 12 个格式页作为保守成本目标，但不能把它说成已经得到编辑部确认的
硬上限。若 PDF 超过 12 页，不要擅自删掉限制说明或实验细节；先查看实际页数，
再和我一起做有证据约束的压缩，并等待编辑部书面答复。

当前授权不包括在 JISE 投稿系统中上传 PDF、点击提交、填写版权协议或支付费用。

## 9. 常见问题

### `File JISE.sty not found`

说明你只上传了部分文件。重新上传整个 ZIP，确认 `JISE.sty` 与 `main.tex` 在项目
根目录。

### `I couldn't open style file JISEbib.bst`

确认 `JISEbib.bst` 位于根目录，文件名大小写完全一致；然后选择
**Recompile from scratch**。

### 引用显示为 `[?]`

确认 `references.bib` 已上传，编译器为 PDFLaTeX，并执行
**Recompile from scratch**。不要手工创建 `.bbl` 来掩盖问题。

### 表格伸出右边界

把 Overleaf 日志中的 `Overfull \\hbox` 行号和 PDF 截图发给我。我会在不改变数据
的前提下调整列宽或排版。

### 想加入作者照片和简介

官方示例在参考文献后含作者简介和照片，但当前工程没有可靠的个人资料。先确认
本次投稿阶段是否要求，再提供每位作者批准的简介和至少 300 dpi 照片。
