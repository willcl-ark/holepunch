#!/usr/bin/env python3
# Copyright (c)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Small network helpers shared by the prototype scripts."""

from __future__ import annotations

import argparse
import socket
from typing import Any


Address = tuple[Any, ...]


def parse_host_port(value: str) -> tuple[str, int]:
    if value.startswith("["):
        end = value.find("]")
        if end == -1 or len(value) <= end + 2 or value[end + 1] != ":":
            raise argparse.ArgumentTypeError(f"invalid endpoint: {value}")
        host = value[1:end]
        port_text = value[end + 2 :]
    else:
        if ":" not in value:
            raise argparse.ArgumentTypeError(f"missing port in endpoint: {value}")
        host, port_text = value.rsplit(":", 1)

    try:
        port = int(port_text)
    except ValueError as err:
        raise argparse.ArgumentTypeError(f"invalid port in endpoint: {value}") from err

    if port < 0 or port > 65535:
        raise argparse.ArgumentTypeError(f"port out of range in endpoint: {value}")

    return host, port


def resolve_endpoint(
    value: str,
    family: int = socket.AF_UNSPEC,
    socktype: int = socket.SOCK_DGRAM,
) -> Address:
    host, port = parse_host_port(value)
    infos = socket.getaddrinfo(host, port, family, socktype)
    if not infos:
        raise OSError(f"could not resolve {value}")
    return infos[0][4]


def short_addr(addr: Address) -> str:
    host, port = addr[0], addr[1]
    if ":" in host and not host.startswith("["):
        return f"[{host}]:{port}"
    return f"{host}:{port}"


def socket_addr(sock: socket.socket) -> str:
    try:
        return short_addr(sock.getsockname())
    except OSError as err:
        return f"<closed: {err}>"


def make_udp_socket(bind_value: str) -> socket.socket:
    bind_addr = resolve_endpoint(bind_value)
    family = socket.AF_INET6 if len(bind_addr) == 4 else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            pass
    sock.bind(bind_addr)
    return sock


def make_tcp_listener(bind_addr: Address) -> socket.socket:
    family = socket.AF_INET6 if len(bind_addr) == 4 else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            pass
    sock.bind(bind_addr)
    sock.listen(1)
    sock.setblocking(False)
    return sock


def make_tcp_connector(bind_addr: Address, peer: Address) -> socket.socket:
    family = socket.AF_INET6 if len(bind_addr) == 4 else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            pass
    sock.bind(bind_addr)
    sock.setblocking(False)
    sock.connect_ex(peer)
    return sock
