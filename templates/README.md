# PPT 模板目录

将商业母版文件放到此目录，并命名为 `default_master.pptx`，系统会自动优先加载。

也可以在后端 `/api/ppt/generate` 请求中传入 `template_path`，指向任意存在的 `.pptx` 文件。生成器会清空模板中的示例页，保留母版尺寸、主题、字体和布局资源，再写入自动生成内容。
