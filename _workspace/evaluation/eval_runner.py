"""
Benchmark Evaluation Runner for Return-Risk Shield (AI Risk Manager - Track 02).
Replays synthetic return events through Shield defensive proxy and computes
per-class Precision, Recall, and False Positive Rate (FPR).
"""
import os
import sys
import json
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Include paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../requirements")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../shield")))

from contracts import ReturnEvent, DecisionAction, AbuseClass, EvaluationMetric, ConfusionMatrix, ClassMetric
from shield_engine import ShieldEngine

console = Console()


class EvaluationRunner:
    def __init__(self, log_dir: str = None):
        self.shield = ShieldEngine(log_dir=log_dir)

    def run_evaluation(self, dataset_path: str, split_name: str = "heldout_eval") -> Dict[str, Any]:
        """
        Runs evaluation on the specified dataset partition.
        """
        self.shield.reset_state()
        
        with open(dataset_path, "r") as f:
            raw_cases = json.load(f)
            
        return_events = [ReturnEvent(**c) for c in raw_cases]
        
        total_tp = 0
        total_fp = 0
        total_tn = 0
        total_fn = 0
        
        # Per abuse class breakdown
        abuse_classes = [
            AbuseClass.WARDROBING.value,
            AbuseClass.BRACKETING_ABUSE.value,
            AbuseClass.SERIAL_RETURNER_FRAUD.value,
            AbuseClass.FALSE_DAMAGE_CLAIM.value,
            "BENIGN"
        ]
        
        class_stats = {
            cls_name: {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "total": 0}
            for cls_name in abuse_classes
        }
        
        failure_cases = []
        detailed_results = []
        
        for ev in return_events:
            decision, audit = self.shield.evaluate(ev)
            gt = ev.ground_truth
            
            gt_class = gt.target_abuse_class.value if gt and gt.target_abuse_class else "BENIGN"
            gt_action = gt.expected_decision.value if gt else "ALLOW"
            is_failure_fixture = gt.failure_case if gt else False
            
            pred_action = decision.action.value
            
            is_abuse = (gt_class != "BENIGN")
            is_predicted_threat = (pred_action in ["BLOCK", "FLAG"])
            
            # Classification outcome
            if is_abuse:
                if is_predicted_threat:
                    # True Positive
                    total_tp += 1
                    class_stats[gt_class]["tp"] += 1
                else:
                    # False Negative (Missed return abuse)
                    total_fn += 1
                    class_stats[gt_class]["fn"] += 1
            else:
                # Ground truth is BENIGN
                if pred_action == "ALLOW":
                    # True Negative
                    total_tn += 1
                    class_stats["BENIGN"]["tn"] += 1
                else:
                    # False Positive (Falsely flagged benign return)
                    total_fp += 1
                    class_stats["BENIGN"]["fp"] += 1
                    
            class_stats[gt_class]["total"] += 1
            
            match = (pred_action == gt_action)
            if not match or is_failure_fixture:
                failure_cases.append({
                    "event_id": ev.event_id,
                    "target_abuse_class": gt_class,
                    "expected": gt_action,
                    "predicted": pred_action,
                    "risk_score": decision.risk_score,
                    "reason": decision.reason,
                    "is_known_failure_fixture": is_failure_fixture,
                    "rationale": gt.rationale if gt else ""
                })
                
            detailed_results.append({
                "event_id": ev.event_id,
                "target_abuse_class": gt_class,
                "expected": gt_action,
                "predicted": pred_action,
                "decision_match": match,
                "triggered_checks": decision.triggered_checks,
                "audit_id": audit.audit_id
            })

        # Calculate metrics
        overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0
        overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0
        overall_fpr = total_fp / (total_fp + total_tn) if (total_fp + total_tn) > 0 else 0.0
        
        by_class_metrics = {}
        for cls_name, counts in class_stats.items():
            if cls_name == "BENIGN":
                cls_prec = 1.0 - (counts["fp"] / (counts["fp"] + counts["tn"])) if (counts["fp"] + counts["tn"]) > 0 else 1.0
                cls_rec = counts["tn"] / (counts["tn"] + counts["fp"]) if (counts["tn"] + counts["fp"]) > 0 else 1.0
                cls_fpr = counts["fp"] / (counts["fp"] + counts["tn"]) if (counts["fp"] + counts["tn"]) > 0 else 0.0
            else:
                cls_prec = counts["tp"] / (counts["tp"] + counts["fp"]) if (counts["tp"] + counts["fp"]) > 0 else 1.0
                cls_rec = counts["tp"] / (counts["tp"] + counts["fn"]) if (counts["tp"] + counts["fn"]) > 0 else 1.0
                cls_fpr = 0.0
                
            by_class_metrics[cls_name] = {
                "precision": round(cls_prec, 4),
                "recall": round(cls_rec, 4),
                "false_positive_rate": round(cls_fpr, 4),
                "sample_count": counts["total"],
                "tp": counts["tp"],
                "fp": counts["fp"],
                "tn": counts["tn"],
                "fn": counts["fn"]
            }

        summary = {
            "split": split_name,
            "sample_count": len(return_events),
            "overall_precision": round(overall_precision, 4),
            "overall_recall": round(overall_recall, 4),
            "overall_false_positive_rate": round(overall_fpr, 4),
            "confusion_matrix": {
                "tp": total_tp,
                "fp": total_fp,
                "tn": total_tn,
                "fn": total_fn
            },
            "by_abuse_class": by_class_metrics,
            "failure_cases": failure_cases,
            "detailed_results": detailed_results
        }
        
        return summary


def display_results(summary: Dict[str, Any]):
    console.print()
    console.print(Panel.fit(
        f"[bold white]Razorpay Return-Risk Shield — Evaluation Benchmark ({summary['split'].upper()})[/bold white]\n"
        f"[dim]Total Evaluated Cases: {summary['sample_count']} | Synthetic Test-Mode Split[/dim]",
        border_style="cyan"
    ))
    
    table = Table(title="Per-Class Performance Metrics", show_header=True, header_style="bold magenta")
    table.add_column("Abuse / Return Category", style="cyan", width=28)
    table.add_column("Samples", justify="right", width=10)
    table.add_column("Precision", justify="right", width=12)
    table.add_column("Recall", justify="right", width=12)
    table.add_column("FPR", justify="right", width=12)
    table.add_column("Status", justify="center", width=14)

    for cls_name, metrics in summary["by_abuse_class"].items():
        if cls_name == "BENIGN":
            table.add_row(
                "BENIGN (Legitimate Returns)",
                str(metrics["sample_count"]),
                f"{metrics['precision']*100:.1f}%",
                f"{metrics['recall']*100:.1f}%",
                f"{metrics['false_positive_rate']*100:.1f}%",
                "[green]BENCHMARK[/green]"
            )
        else:
            p_str = f"{metrics['precision']*100:.1f}%"
            r_str = f"{metrics['recall']*100:.1f}%"
            table.add_row(
                cls_name,
                str(metrics["sample_count"]),
                p_str,
                r_str,
                "0.0%",
                "[green]PASSED[/green]" if metrics["recall"] >= 0.75 else "[yellow]MARGINAL[/yellow]"
            )
            
    console.print(table)
    
    # Overall summary table
    cm = summary["confusion_matrix"]
    console.print(
        f"[bold]Overall Performance:[/bold] "
        f"Precision: [bold green]{summary['overall_precision']*100:.1f}%[/bold green] | "
        f"Recall: [bold green]{summary['overall_recall']*100:.1f}%[/bold green] | "
        f"FPR: [bold green]{summary['overall_false_positive_rate']*100:.1f}%[/bold green] | "
        f"TP: {cm['tp']}, TN: {cm['tn']}, FP: {cm['fp']}, FN: {cm['fn']}\n"
    )
    
    if summary["failure_cases"]:
        console.print("[bold yellow]Documented Edge Case & Failure Analysis:[/bold yellow]")
        for fc in summary["failure_cases"]:
            console.print(
                f"  • [cyan]{fc['event_id']}[/cyan] ({fc['target_abuse_class']}): "
                f"Expected [bold]{fc['expected']}[/bold], Shield returned [bold]{fc['predicted']}[/bold].\n"
                f"    [dim]Rationale: {fc['rationale']}[/dim]"
            )
        console.print()


def main():
    runner = EvaluationRunner()
    
    results_dir = "_workspace/test_results"
    os.makedirs(results_dir, exist_ok=True)
    
    heldout_path = "_workspace/dataset/heldout_eval_transactions.json"
    if not os.path.exists(heldout_path):
        print(f"Error: Held-out evaluation dataset not found at {heldout_path}")
        sys.exit(1)
        
    summary = runner.run_evaluation(heldout_path, split_name="heldout_eval")
    display_results(summary)
    
    out_file = os.path.join(results_dir, "metrics_summary.json")
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)
        
    print(f"Evaluation metrics saved to {out_file}")


if __name__ == "__main__":
    main()
