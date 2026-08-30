---
title: Talent Bench
emoji: 🎯
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 6.26.0
app_file: app.py
short_description: Search the Talent Bench factory job-board demo
python_version: "3.12"
startup_duration_timeout: 30m
---

# Talent Bench

Interactive demo of the **local** Business Factory example at
`businesses/examples/talent-bench`.

The kernel pipeline is four methods — `sync`, `build`, `validate`, `distribute` —
now also runnable as a Temporal Workflow. This Space searches a snapshot of the
board those methods produce (Mercor, Outlier, DataAnnotation).

Source repo: [business-factory](https://github.com/dynamicoscilator369/business-factory).
