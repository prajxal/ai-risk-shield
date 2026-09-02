"""
End-to-End Integration Demo Script for Return-Risk Shield (AI Risk Manager - Track 02).
Simulates realistic return scenarios against the live Shield Defensive Proxy.
"""
import sys
import os
import json
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

BASE_URL = "http://127.0.0.1:8000"


def run_demo():
    console.print()
    console.print(Panel.fit(
        "[bold white]Razorpay Return-Risk Shield — Pitch Demonstration[/bold white]\n"
        "[dim]Track 02: AI Risk Manager • Return Abuse & Loss Prevention Defensive Proxy[/dim]",
        border_style="cyan"
    ))

    # 1. Health check
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=3).json()
        console.print(f"[green]✓[/green] Connected to Shield Proxy: [bold]{health.get('service')}[/bold] (mode: {health.get('mode')})")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to connect to Shield Proxy at {BASE_URL}: {e}")
        return

    # 2. Fetch scenarios
    scenarios = requests.get(f"{BASE_URL}/scenarios").json()
    console.print(f"[green]✓[/green] Loaded {len(scenarios)} demonstration scenarios\n")

    table = Table(title="Live Evaluation Results", show_header=True, header_style="bold magenta")
    table.add_column("Scenario", style="cyan", width=34)
    table.add_column("Expected", justify="center", width=12)
    table.add_column("Shield Verdict", justify="center", width=22)
    table.add_column("Risk Score", justify="right", width=12)
    table.add_column("Audit ID", style="dim", width=18)

    for sc in scenarios:
        ev = sc.get("return_event") or sc.get("transaction")
        res = requests.post(f"{BASE_URL}/returns/evaluate", json=ev)
        
        expected_badge = sc["badge"]
        if res.status_code == 200:
            data = res.json()
            verdict = data.get("status", "AUTHORIZED")
            risk = data.get("decision", {}).get("risk_score", 0)
            audit_id = data.get("audit_id", "N/A")
            v_style = "[green]AUTHORIZED (200)[/green]" if verdict == "AUTHORIZED" else "[yellow]FLAGGED (200)[/yellow]"
        elif res.status_code == 403:
            data = res.json().get("detail", {})
            verdict = "BLOCKED"
            risk = data.get("risk_score", 100)
            audit_id = data.get("audit_id", "N/A")
            v_style = "[red]BLOCKED (403)[/red]"
        else:
            v_style = f"[red]ERROR {res.status_code}[/red]"
            risk = "N/A"
            audit_id = "N/A"

        table.add_row(
            sc["name"],
            expected_badge,
            v_style,
            f"{risk}/100" if isinstance(risk, (int, float)) else str(risk),
            audit_id
        )

    console.print(table)
    console.print("\n[bold green]✓ Live demonstration run complete.[/bold green]\n")


if __name__ == "__main__":
    run_demo()
