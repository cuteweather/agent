# Contributing

欢迎提交 issue 和 pull request。

## 开发约定

- 每个 skill 放在独立目录下，目录名与 frontmatter 里的 `name` 保持一致。
- 每个 skill 至少包含一个 `SKILL.md`。
- 新增 `scripts/`、`references/`、`assets/` 时，只放与该 skill 直接相关的内容。
- 修改或新增 skill 后，重新生成根目录 `skills.json`：

```powershell
python .\scripts\generate_skill_index.py
```

## 提交前检查

运行：

```powershell
python .\scripts\check_repo.py
```

该脚本会检查：

- `SKILL.md` frontmatter 是否完整
- `skills.json` 是否与当前目录一致
- 是否存在常见明文密钥模式

## Pull Request 建议

- 在标题里说明受影响的 skill 名称。
- 如果改动影响使用方式，请同步更新 `README.md` 或对应 skill 的 `SKILL.md`。
- 如果新增脚本，请尽量保持无状态、可重复执行，并避免写死本机路径或明文凭据。
