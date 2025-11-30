from pprint import pprint

import brevo_python
from brevo_python.rest import ApiException

# Configure API key authorization: api-key
configuration = brevo_python.Configuration()
configuration.api_key["api-key"] = ""

content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>驗證您的郵箱</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background: #f9f9f9; }
        .container { background: white; border-radius: 8px; padding: 30px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #007bff; padding-bottom: 20px; }
        .header h1 { margin: 0; color: #1a1a1a; font-size: 28px; }
        .header p { margin: 10px 0 0 0; color: #666; font-size: 14px; }
        .content { text-align: center; margin: 30px 0; }
        .content p { color: #444; font-size: 16px; line-height: 1.8; margin: 15px 0; }
        .verification-code { background: #f0f7ff; padding: 20px; border-radius: 4px; margin: 20px 0; }
        .code { font-family: 'Courier New', monospace; font-size: 24px; font-weight: bold; color: #007bff; letter-spacing: 2px; }
        .button-container { margin: 30px 0; }
        .verify-button { background: #007bff; color: white; padding: 12px 40px; border-radius: 4px; text-decoration: none; font-weight: bold; display: inline-block; }
        .verify-button:hover { background: #0056b3; }
        .warning { color: #dc3545; font-size: 14px; margin-top: 20px; }
        .footer { text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✉️ 驗證您的郵箱</h1>
            <p>Periscope - 個人每日閱讀文摘</p>
        </div>

        <div class="content">
            <p>感謝您註冊 Periscope！</p>
            <p>為了完成您的帳戶設置，請驗證您的郵箱地址。</p>

            <div class="verification-code">
                <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">您的驗證碼：</p>
                <div class="code">{{ verification_code }}</div>
            </div>

            <p>或點擊下方按鈕進行驗證：</p>
            <div class="button-container">
                <a href="{{ verification_link }}" class="verify-button">驗證郵箱</a>
            </div>

            <p style="font-size: 14px; color: #666;">此驗證碼將在 24 小時後過期。</p>
            <p class="warning">⚠️ 如果您沒有註冊此帳戶，請忽略此郵件。</p>
        </div>

        <div class="footer">
            <p>© 2025 Periscope. 版權所有。</p>
            <p>如有問題，請聯繫我們的支持團隊。</p>
        </div>
    </div>
</body>
</html>
"""

api_instance = brevo_python.TransactionalEmailsApi(brevo_python.ApiClient(configuration))
send_smtp_email = brevo_python.SendSmtpEmail(
    sender=brevo_python.SendSmtpEmailSender(
        email="brewie@brewie.qzz.io",
    ),
    to=[
        brevo_python.SendSmtpEmailTo(
            email="puchen.tw@gmail.com",
        ),
    ],
    subject="Your Daily Reading Digest",
    html_content=content,
)  # SendSmtpEmail | Values to send a transactional email

try:
    # Send a transactional email
    api_response = api_instance.send_transac_email(send_smtp_email)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling TransactionalEmailsApi->send_transac_email: %s\n" % e)
