# 🚀 Stabilizer Finance BOT

> Automated volume farming on Stabilizer Finance testnet for efficient SP point accumulation

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Stars](https://img.shields.io/github/stars/hourx/Stabilizer-Finance-BOT.svg)

---

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [✨ Features](#-features)
- [📋 Requirements](#-requirements)
- [🛠 Installation](#-installation)
- [⚙️ Configuration](#%EF%B8%8F-configuration)
- [🚀 Usage](#-usage)
- [🌐 Proxy Recommendation](#-proxy-recommendation)
- [💖 Support the Project](#-support-the-project)
- [🤝 Contributing](#-contributing)
- [📞 Contact](#-contact)

---

## 🎯 Overview

Stabilizer Finance BOT is an automated volume farming tool designed for the Stabilizer Finance testnet. It executes round-trip swaps (e.g., USDT ↔ USDZ) through the Router contract to accumulate SP (Stability Points) efficiently, automatically stopping when the daily cap is reached.

---

## ✨ Features

- 🔄 **Auto-Swap** — Automated round-trip token swaps via Router contract
- 🪙 **Multi-Token Support** — USDT, USDC, USDS, PYUSD, USDZ
- 📊 **SP Status Tracking** — Real-time monitoring of SP points and ranking
- 🔐 **Proxy Support** — HTTP and SOCKS5 proxy support with round-robin assignment
- 👥 **Multi-Account** — Process multiple wallets from accounts.txt
- ⚡ **Gas Efficient** — Large swap amounts ($50K default) for optimal gas usage
- 🛡️ **Smart Approvals** — Auto-approve tokens only when needed
- 🎨 **Colorful Logging** — Beautiful terminal output with colorama

---

## 📋 Requirements

- Python 3.9 or higher
- Ethereum wallet(s) with testnet tokens on Sepolia
- RPC endpoint (default: PublicNode Sepolia)

---

## 🛠 Installation

1. Clone the repository:

```bash
git clone https://github.com/hourx/Stabilizer-Finance-BOT.git
cd Stabilizer-Finance-BOT
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### accounts.txt

Add your wallet private keys (one per line):

```
0xYourPrivateKey1
0xYourPrivateKey2
```

### proxy.txt

Add proxies (optional, one per line):

```
http://ip:port
socks5://ip:port
```

### .env

Configure swap parameters:

```env
SWAP_AMOUNT=50000      # Amount per swap in USD
DAILY_CAP=20000        # Daily SP cap target
RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
```

---

## 🚀 Usage

Run the bot:

```bash
python bot.py
```

You will see an interactive menu:

```
[ MENU ] ══════════════════════════════════
[1] Check SP Status
[2] Approve Tokens
[3] Volume Farm (Auto-Swap)
[4] Run All Features
```

- **Option 1**: Check current SP points, rank, and daily progress
- **Option 2**: Approve all tokens for Router spending
- **Option 3**: Run automated volume farming until daily cap
- **Option 4**: Execute all features in sequence

---

## 🌐 Proxy Recommendation

For better rate limits and stability, consider using residential proxies:

- [Smartproxy](https://smartproxy.com)
- [Bright Data](https://brightdata.com)
- [IPRoyal](https://iproyal.com)

---

## 💖 Support the Project

If you find this tool helpful, consider supporting development:

**EVM Wallet (Ethereum/Sepolia):**
```
0x50fC87A287A5ab6B16e8d1780b8533468Ae1baAA
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Contact

- **GitHub:** [hourx](https://github.com/hourx)

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/hourx">hourx</a>
</p>
