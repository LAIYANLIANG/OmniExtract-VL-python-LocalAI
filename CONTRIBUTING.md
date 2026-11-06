# Contributing to OmniExtract-VL

Thank you for your interest in contributing to **OmniExtract-VL**! We welcome all contributions from bug fixes, new vendor extractors, documentation improvements to performance optimizations.

---

## 🛠️ Development Workflow

1. **Fork the Repository**: Create your personal fork on GitHub.
2. **Clone Locally**:
   ```bash
   git clone https://github.com/your-username/OmniExtract-VL-python-LocalAI.git
   cd OmniExtract-VL-python-LocalAI
   ```
3. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/new-vendor-extractor
   ```
4. **Make Your Changes**:
   - Write clean, type-annotated code.
   - Ensure **no sensitive documents, private credentials, or personal information** are included in your commits.
5. **Run Tests & Verify**:
   - Verify the 7-step pipeline works with synthetic or de-identified test data.
6. **Submit a Pull Request (PR)**:
   - Provide a concise description of your changes and why they are needed.

---

## 🔒 Security & Data Privacy Guidelines

- **Never commit real enterprise documents**: Always use synthetic or de-identified sample documents for testing.
- **Do not commit credentials**: Keep all API keys, database credentials, and secrets in `.env` files which are excluded by `.gitignore`.
- If you discover a potential security vulnerability, please open a private security advisory rather than a public issue.

---

## 🌐 Community & Code of Conduct

Please be respectful, collaborative, and constructive when engaging in issues, pull requests, and discussions.

Thank you for making **OmniExtract-VL** better for everyone!

