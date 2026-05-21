from __future__ import annotations

import textwrap

from language_tutor.schemas import ProgressMarkdownExport, ProgressReport

WRAP_WIDTH = 100


def _line(label: str, value: object) -> str:
    return f"- {label}: {value}"


def _wrap_bullet(text: str) -> list[str]:
    return textwrap.wrap(
        f"- {text}",
        width=WRAP_WIDTH,
        subsequent_indent="  ",
        break_long_words=False,
        break_on_hyphens=False,
    ) or ["-"]


def render_progress_markdown(report: ProgressReport) -> ProgressMarkdownExport:
    lines: list[str] = [
        "# Progress Report",
        "",
        _line("Generated at", report.generated_at.isoformat()),
        _line(
            "Window",
            f"{report.report_window.actual_session_count}/{report.report_window.requested_session_count} sessions",
        ),
    ]
    if report.report_window.start_date or report.report_window.end_date:
        lines.append(
            _line(
                "Date range",
                f"{report.report_window.start_date or 'unavailable'} to {report.report_window.end_date or 'unavailable'}",
            )
        )
    lines.extend(["", "## Snapshot"])
    snapshot = report.snapshot
    lines.extend(
        [
            _line("Streak", snapshot.streak_days),
            _line("Due vocabulary", snapshot.due_count),
            _line("Maturity", snapshot.maturity or "none"),
            _line("Weak patterns", ", ".join(snapshot.top_weak_patterns) or "none"),
            _line("Cost status", snapshot.cost_status),
            _line("Next action", snapshot.next_action),
        ]
    )
    if snapshot.month_to_date_estimated_usd is not None:
        lines.append(_line("Month-to-date estimated USD", f"{snapshot.month_to_date_estimated_usd:.4f}"))

    lines.extend(["", "## Tag Mastery"])
    if not report.tag_mastery:
        lines.append("- No mastery evidence yet.")
    for row in report.tag_mastery:
        stale = " stale" if row.stale else ""
        lines.extend(
            _wrap_bullet(
                f"{row.tag}: {row.score} ({row.band}, {row.trend}{stale}, "
                f"{row.evidence_count} evidence) - {row.next_practice_hint}"
            )
        )

    recap = report.recent_recap
    lines.extend(["", "## Recent Recap"])
    if recap.actual_session_count == 0:
        lines.append("- No completed analyzed sessions yet.")
    else:
        lines.extend(
            [
                _line("Answers", recap.practice_totals.answers),
                _line("Vocabulary reviews", recap.practice_totals.vocabulary_reviews),
                _line("Writing answers", recap.practice_totals.writing_answers),
            ]
        )
        for label, value in (
            ("Reading answers", recap.practice_totals.reading_answers),
            ("Lesson answers", recap.practice_totals.lesson_answers),
            ("Transcript drills", recap.practice_totals.transcript_drills),
        ):
            if value:
                lines.append(_line(label, value))
        lines.extend(
            [
                _line("Due reviews completed", recap.due_review_completion.completed),
                _line(
                    "Mistake severity",
                    f"low {recap.mistake_severity_totals.low}, "
                    f"medium {recap.mistake_severity_totals.medium}, "
                    f"high {recap.mistake_severity_totals.high}",
                ),
                _line("Weak tags new", ", ".join(recap.weak_tag_changes.new) or "none"),
                _line("Weak tags repeated", ", ".join(recap.weak_tag_changes.repeated) or "none"),
                _line("Weak tags resolved", ", ".join(recap.weak_tag_changes.resolved) or "none"),
            ]
        )
        if recap.latest_session_summary:
            lines.extend(_wrap_bullet(f"Latest summary: {recap.latest_session_summary}"))

    lines.extend(["", "## Trends"])
    for trend in recap.trends:
        lines.append(
            _line(
                trend.label,
                f"{trend.direction}; {trend.sparkline or 'no data'}; {trend.min_label}; {trend.max_label}",
            )
        )

    lines.extend(["", "## Due Review"])
    lines.extend(
        [
            _line("Due count", report.due_review_summary.due_count),
            _line("Completed in window", report.due_review_summary.completed_in_window),
            _line("Low quality in window", report.due_review_summary.low_quality_in_window),
        ]
    )

    notices = report.skipped_data or recap.skipped_data
    lines.extend(["", "## Skipped Data"])
    if not notices:
        lines.append("- None.")
    for notice in notices:
        lines.extend(_wrap_bullet(f"{notice.scope}: {notice.message}"))

    lines.extend(["", "## Scope Guardrails"])
    for guardrail in report.scope_guardrails:
        lines.append(f"- {guardrail}")

    return ProgressMarkdownExport(
        generated_at=report.generated_at,
        report_window=report.report_window,
        markdown="\n".join(lines) + "\n",
    )
