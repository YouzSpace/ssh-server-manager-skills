#!/usr/bin/env python3
"""
ssh_helper.py - SSH 服务器管理辅助工具

用法：
  python3 ssh_helper.py test   --host <IP> --user <user> --key <私钥路径>
  python3 ssh_helper.py exec   --host <IP> --user <user> --key <私钥路径> --cmd "uptime"
  python3 ssh_helper.py info   --host <IP> --user <user> --key <私钥路径>
  python3 ssh_helper.py upload --host <IP> --user <user> --key <私钥路径> --local ./file --remote /tmp/file
  python3 ssh_helper.py download --host <IP> --user <user> --key <私钥路径> --remote /tmp/file --local ./file
"""

import argparse
import subprocess
import sys


def build_ssh_base(host, user, key_path, port=22):
    """构建 SSH 基础参数列表"""
    return [
        "ssh",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=15",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=3",
        "-p", str(port),
        f"{user}@{host}",
    ]


def run_cmd(cmd, check=False):
    """执行命令并返回结果"""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result


def cmd_test(args):
    """测试 SSH 连通性"""
    ssh_cmd = build_ssh_base(args.host, args.user, args.key, args.port)
    ssh_cmd.append("echo ok")
    result = run_cmd(ssh_cmd)
    if result.returncode == 0 and "ok" in result.stdout:
        print("SSH 连接成功")
    else:
        print("SSH 连接失败", file=sys.stderr)
        sys.exit(1)


def cmd_exec(args):
    """执行远程命令"""
    ssh_cmd = build_ssh_base(args.host, args.user, args.key, args.port)
    ssh_cmd.append(args.cmd)
    run_cmd(ssh_cmd, check=True)


def cmd_info(args):
    """采集服务器信息"""
    ssh_cmd = build_ssh_base(args.host, args.user, args.key, args.port)
    info_cmd = (
        "echo '=== 系统信息 ===' && uname -a && "
        "echo '=== 系统版本 ===' && cat /etc/os-release 2>/dev/null | head -5 && "
        "echo '=== 内存使用 ===' && free -h && "
        "echo '=== 磁盘使用 ===' && df -h / && "
        "echo '=== 运行时间 ===' && uptime && "
        "echo '=== 运行中的服务 ===' && systemctl list-units --type=service --state=running 2>/dev/null | head -20 && "
        "echo '=== 监听端口 ===' && ss -tlnp 2>/dev/null | head -20"
    )
    ssh_cmd.append(info_cmd)
    run_cmd(ssh_cmd, check=True)


def cmd_upload(args):
    """上传文件到服务器"""
    scp_cmd = [
        "scp",
        "-i", args.key,
        "-o", "StrictHostKeyChecking=no",
        "-P", str(args.port),
        args.local,
        f"{args.user}@{args.host}:{args.remote}",
    ]
    result = run_cmd(scp_cmd)
    if result.returncode == 0:
        ssh_cmd = build_ssh_base(args.host, args.user, args.key, args.port)
        ssh_cmd.append(f"ls -lh {args.remote}")
        run_cmd(ssh_cmd)


def cmd_download(args):
    """从服务器下载文件"""
    scp_cmd = [
        "scp",
        "-i", args.key,
        "-o", "StrictHostKeyChecking=no",
        "-P", str(args.port),
        f"{args.user}@{args.host}:{args.remote}",
        args.local,
    ]
    run_cmd(scp_cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description="SSH Server Manager Helper")
    parser.add_argument("--host", required=True, help="服务器 IP 或域名")
    parser.add_argument("--user", default="root", help="SSH 用户名 (默认 root)")
    parser.add_argument("--key", required=True, help="SSH 私钥路径")
    parser.add_argument("--port", type=int, default=22, help="SSH 端口 (默认 22)")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # test
    subparsers.add_parser("test", help="测试 SSH 连通性")

    # exec
    exec_parser = subparsers.add_parser("exec", help="执行远程命令")
    exec_parser.add_argument("--cmd", required=True, help="要执行的命令")

    # info
    subparsers.add_parser("info", help="采集服务器信息")

    # upload
    upload_parser = subparsers.add_parser("upload", help="上传文件到服务器")
    upload_parser.add_argument("--local", required=True, help="本地文件路径")
    upload_parser.add_argument("--remote", required=True, help="远程文件路径")

    # download
    download_parser = subparsers.add_parser("download", help="从服务器下载文件")
    download_parser.add_argument("--remote", required=True, help="远程文件路径")
    download_parser.add_argument("--local", required=True, help="本地文件路径")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "test": cmd_test,
        "exec": cmd_exec,
        "info": cmd_info,
        "upload": cmd_upload,
        "download": cmd_download,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
