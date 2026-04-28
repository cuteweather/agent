# Security

## Supported Use

这个仓库面向 skill 定义、辅助脚本和参考资料管理，不应提交任何真实生产凭据。

## Secrets

请不要提交：

- API keys
- Access tokens
- Passwords
- 私有服务地址中附带的认证信息

当前仓库中的相关脚本使用环境变量读取敏感信息，例如：

- `PEXELS_API_KEY`
- `MINIMAX_API_KEY`
- `MINIMAX_API_URL`

## Reporting

如果你发现仓库中存在疑似泄露的密钥、令牌或其他敏感信息：

1. 不要公开开 issue 粘贴密钥内容。
2. 立即通知仓库维护者。
3. 建议同时轮换对应凭据。
