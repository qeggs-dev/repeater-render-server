# Render API

将 Markdown 文本转换为图片进行输出

- **`/render`**
  - **Requset**
    - **method:** `POST`
    - **type:** `JSON`
    - **Request Body**:
      - `content` (str): 要渲染的 HTML 文本（必填）
      - `image_expiry_time` (float): 图片链接有效时长
      - `width` (int): 图片宽度
      - `height` (int): 图片高度
      - `quality` (int): 图片质量
  - **Response**
    - **type:** `JSON`
    - **Response Body**:
      - `image_url` (str): 图片渲染输出文件URL
      - `file_uuid` (str): 图片渲染输出文件的UUID
      - `status` (str): 渲染处理器的状态，只有`success`,`failed`和`pending`三种状态
      - `browser_used` (str): 渲染使用的浏览器
      - `url_expiry_time` (float): 图片链接有效时长
      - `error` (str): 渲染错误信息
      - `content` (str): 渲染的文本
      - `image_render_time_ms` (float): 图片渲染时间（毫秒）
      - `created` (int): 图片渲染输出文件的创建时间戳
      - `created_ms` (int): 图片渲染输出文件的创建时间戳（毫秒）
      - `details_time`
        - `preprocess` (int): 预处理时间（纳秒）
        - `render` (int): HTML 渲染耗时（纳秒）

你需要**保证你提供的 HTML 输入是安全的**
否则攻击者可能会通过它们进行 XSS 攻击，注入恶意代码