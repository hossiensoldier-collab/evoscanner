پروژه EvoScanner — یادگیری و پیاده‌سازی قابلیت: RAG (Retrieval-Augmented Generation)

## قابلیت مورد نظر

**نام:** RAG (Retrieval-Augmented Generation)
**توضیح:** پاسخ به سؤال از منابع

## منابع مرتبط (از پایگاه خودم)

  - [github] fastapi/fastapi — https://github.com/fastapi/fastapi
  - [github] encode/httpx — https://github.com/encode/httpx
  - [github] huggingface/transformers — https://github.com/huggingface/transformers
  - [github] gradio-app/gradio — https://github.com/gradio-app/gradio
  - [github] pydantic/pydantic — https://github.com/pydantic/pydantic
  - [github] pydantic/pydantic-ai — https://github.com/pydantic/pydantic-ai
  - [github] fastapi/typer — https://github.com/fastapi/typer
  - [github] localstack/localstack — https://github.com/localstack/localstack
  - [github] getsentry/sentry — https://github.com/getsentry/sentry
  - [github] saleor/saleor — https://github.com/saleor/saleor

## تکنیک‌های استخراج‌شده



## قطعات کد موجود


### encode/httpx
```
Which now allows us to use HTTPX directly from the command-line...

<p align="center">
  <img width="700" src="docs/img/httpx-help.png" alt='httpx --help'>
</p>

Sending a request...

<p align="center">
  <img width="700" src="docs/img/httpx-request.png" alt='httpx http://httpbin.org/json'>
</p>

## Features

HTTPX builds on the well-established usability of `requests`, and gives you:

* A broadly
```

### webdataset/webdataset
```
bucket = "https://storage.googleapis.com/webdataset/testdata/"
dataset = "publaynet-train-{000000..000009}.tar"

url = bucket + dataset
!curl -s {bucket}publaynet-train-000000.tar | dd count=5000 2> /dev/null | tar tf - 2> /dev/null | sed 10q
```

### pymupdf/PyMuPDF
```
Wheels are available for **Windows**, **macOS**, and **Linux** on Python 3.10–3.14. If no pre-built wheel exists for your platform, pip will compile from source (requires a C/C++ toolchain).

### Optional extras

| Package | Purpose |
|---|---|
| `pymupdf-fonts` | Extended font collection for text output |
| `pymupdf4llm` | LLM/RAG-optimised Markdown and JSON extraction |
| `pymupdfpro` | Adds Off
```


## فایل‌های پروژه که این قابلیت را دارند

  - feature_rag_v2.py

## درخواست من

لطفاً:

۱. **تحلیل عمیق** — این قابلیت چطور کار می‌کند، چه الگوریتمی دارد
۲. **بهترین منابع** — از لیست بالا، کدام‌ها را بخوانم و به چه ترتیب
۳. **پیاده‌سازی از صفر** — اگر بخواهم این قابلیت را از ابتدا بسازم
۴. **پیشنهادهای بهبود** — پروژه فعلی چه چیزی کم دارد
۵. **کد نمونه** — مثال ساده برای درک بهتر

محیط: Termux اندروید، فقط stdlib پایتون

هدف: من می‌خواهم این قابلیت را کامل یاد بگیرم و بهتر پیاده کنم.

