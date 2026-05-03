# SSH 服务器操作

## 查看服务器状态

```bash
ssh -i <私钥> <user>@<IP> "uptime && free -h && df -h / && docker ps 2>/dev/null"
```

输出关键指标：运行时间、内存使用、磁盘占用、运行中的容器。

## 执行任意命令

```bash
ssh -i <私钥> <user>@<IP> "<command>"
```

执行前向用户确认命令内容，执行后输出结果。

## 上传文件

```bash
scp -i <私钥> <本地文件> <user>@<IP>:<远程路径>
```

上传后验证文件存在：`ssh -i <私钥> <user>@<IP> "ls -lh <远程路径>"`

## 下载文件

```bash
scp -i <私钥> <user>@<IP>:<远程文件> <本地路径>
```

## 执行本地脚本

```bash
ssh -i <私钥> <user>@<IP> "bash -s" < <本地脚本文件>
```
