# Issue #017: Add Comprehensive Metrics Collection System

## Description
Implement a metrics collection system to track agent performance, system health, and business metrics. This will provide visibility into system behavior and help identify optimization opportunities.

## Requirements

### Core Implementation
- [ ] Create `core/metrics_collector.py` with MetricsCollector class
- [ ] Support different metric types (counter, gauge, histogram, summary)
- [ ] Implement metric aggregation over time windows
- [ ] Add metric export in multiple formats (Prometheus, JSON, StatsD)
- [ ] Include metric namespacing and tagging

### Metrics to Track
- [ ] Agent execution time (histogram)
- [ ] Success/failure rates (counter)
- [ ] Queue depths (gauge)
- [ ] Memory usage (gauge)
- [ ] API call counts per service (counter)
- [ ] Cache hit rates (gauge)
- [ ] Error rates by type (counter)
- [ ] Concurrent agent count (gauge)

### Features
- [ ] Real-time metric streaming
- [ ] Historical metric storage (rolling window)
- [ ] Alerting thresholds and callbacks
- [ ] Metric sampling for high-frequency events
- [ ] Custom metric registration API

### Export Formats
- [ ] Prometheus exposition format for scraping
- [ ] StatsD protocol for push metrics
- [ ] JSON API endpoint for dashboards
- [ ] CSV export for analysis

## Example Usage

```python
from core.metrics_collector import MetricsCollector, Metric

# Initialize collector
metrics = MetricsCollector()

# Register metrics
request_duration = metrics.histogram(
    "agent_request_duration_seconds",
    "Time to process agent request",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

error_count = metrics.counter(
    "agent_errors_total",
    "Total number of agent errors",
    labels=["agent_type", "error_type"]
)

# Record metrics
with request_duration.time():
    process_request()

error_count.labels(agent_type="smart_issue", error_type="timeout").inc()

# Export metrics
prometheus_data = metrics.export_prometheus()
```

## Acceptance Criteria
- [ ] Metrics collection adds < 1% overhead to operations
- [ ] Prometheus endpoint returns valid metrics format
- [ ] All core metrics are tracked accurately
- [ ] Memory usage for metrics stays under 10MB for 1hr window
- [ ] Integration with existing telemetry system works
- [ ] Dashboard can visualize exported metrics

## Technical Notes
- Use thread-safe counters and locks for metrics
- Implement efficient circular buffers for histograms
- Consider using mmap for persistent metrics
- Add configuration for metric retention periods