#!/usr/bin/env python3
"""
ssh_helper.py - 辅助生成 SSH 连接命令
用法：
  python3 ssh_helper.py --host 192.168.1.100 --user root --key ~/.ssh/id_ed25519_workbuddy --cmd "uptime"
"""

import argparse
import subprocess
import sys

def build_ssh_command(host, user, key_path, cmd, port=22):
    """构建 ssh 命令"""
    ssh_cmd = [
        "ssh",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=15",
        "-p", str(port),
        f"{user}@{host}",
        cmd
    ]
    return ssh_cmd

def main():
    parser = argparse.ArgumentParser(description="SSH Server Manager Helper")
    parser.add_argument("--host", required=True, help="服务器 IP 或域名")
    parser.add_argument("--user", default="root", help="SSH 用户名 (默认 root)")
    parser.add_argument("--key", required=True, help="SSH 私钥路径")
    parser.add_argument("--port", type=int, default=22, help="SSH 端口 (默认 22)")
    parser.add_argument("--cmd", required=True, help="要在服务器上执行的命令")
    parser.add_argument("--run", action="store_true", help="直接执行命令（默认只打印）")
    
    args = parser.parse_args()
    
    cmd = build_ssh_command(args.host, args.user, args.key, args.cmd, args.port)
    
    if args.run:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    else:
        print(" ".join(cmd))

if __name__ == "__main__":
    main()
