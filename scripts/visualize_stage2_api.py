#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stage 2 API Flow Visualization - HTML interactive diagram.
Shows request flow through rate limiter, backoff, and retries.
"""

import webbrowser
import os
from pathlib import Path
import io
import sys


def generate_html():
    """Generate HTML visualization for Stage 2 API flow."""

    html_content = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SuperMarket Этап 2 - Поток API запросов</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .content {
            padding: 40px;
        }

        .section {
            margin-bottom: 40px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }

        .section h2 {
            font-size: 1.5em;
            margin-bottom: 15px;
            color: #333;
        }

        .flow-diagram {
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
            padding: 20px;
            background: white;
            border-radius: 8px;
            overflow-x: auto;
            margin-top: 15px;
        }

        .flow-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 6px;
            font-weight: bold;
            white-space: nowrap;
            min-width: 140px;
            text-align: center;
        }

        .flow-box.rate-limiter {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }

        .flow-box.backoff {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }

        .flow-box.retry {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }

        .flow-box.error {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }

        .flow-box.success {
            background: linear-gradient(135deg, #30cfd0 0%, #330867 100%);
        }

        .arrow {
            font-size: 1.8em;
            color: #667eea;
            font-weight: bold;
        }

        .decision-box {
            background: #fff3cd;
            border: 2px solid #ffc107;
            padding: 15px;
            border-radius: 6px;
            color: #856404;
            font-weight: bold;
        }

        .component {
            background: white;
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }

        .component h3 {
            color: #667eea;
            margin-bottom: 10px;
        }

        .feature-list {
            list-style: none;
            padding: 0;
        }

        .feature-item {
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .feature-item:last-child {
            border-bottom: none;
        }

        .feature-item::before {
            content: '✓ ';
            color: #28a745;
            font-weight: bold;
        }

        .code-block {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            margin-top: 10px;
        }

        .status-ok {
            color: #28a745;
        }

        .status-error {
            color: #dc3545;
        }

        .status-retry {
            color: #ffc107;
        }

        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }

        .metric-card {
            background: white;
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }

        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }

        .metric-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }

        .footer {
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SuperMarket Этап 2</h1>
            <p>Отказоустойчивый API Клиент</p>
        </div>

        <div class="content">
            <!-- Request Flow -->
            <div class="section">
                <h2>Поток запроса к API</h2>

                <div class="flow-diagram">
                    <div class="flow-box">ЗАПРОС</div>
                    <div class="arrow">→</div>
                    <div class="flow-box rate-limiter">Лимитер</div>
                    <div class="arrow">→</div>
                    <div class="flow-box">httpx.AsyncClient</div>
                    <div class="arrow">→</div>
                    <div class="flow-box retry">Ретрай</div>
                    <div class="arrow">→</div>
                    <div class="flow-box success">ОТВЕТ</div>
                </div>

                <div style="margin-top: 15px; padding: 15px; background: #e7f3ff; border-radius: 6px; border-left: 4px solid #2196F3;">
                    <p><strong>На каждом этапе:</strong></p>
                    <p style="margin-top: 10px;">1. <strong>Лимитер:</strong> проверка rate limit (Token Bucket)</p>
                    <p style="margin-top: 8px;">2. <strong>HTTP запрос:</strong> асинхронный запрос с таймаутом</p>
                    <p style="margin-top: 8px;">3. <strong>Ретрай:</strong> Exponential Backoff + Jitter для 429/5xx</p>
                    <p style="margin-top: 8px;">4. <strong>Результат:</strong> успех или ошибка с ReasonCode</p>
                </div>
            </div>

            <!-- Rate Limiter -->
            <div class="section">
                <h2>Token Bucket Rate Limiter</h2>

                <div class="component">
                    <h3>Как работает:</h3>
                    <ul class="feature-list">
                        <li class="feature-item">Token Bucket algorithm на Redis</li>
                        <li class="feature-item">Fixed-window rate limiting</li>
                        <li class="feature-item">Конфигурируемые лимиты на конфигурацию</li>
                        <li class="feature-item">Возвращает remaining tokens и reset_at</li>
                    </ul>
                </div>

                <div class="flow-diagram">
                    <div class="decision-box">
                        tokens > 0 ?
                    </div>
                    <div class="arrow">→</div>
                    <div class="flow-box" style="background: #28a745;">ДА: Разрешить</div>
                </div>

                <div class="flow-diagram">
                    <div class="decision-box">
                        tokens == 0 ?
                    </div>
                    <div class="arrow">→</div>
                    <div class="flow-box error">НЕТ: RateLimit (429)</div>
                </div>

                <div class="code-block">
allowed, info = rate_limiter.is_allowed(max_requests=100, window_seconds=60)
if not allowed:
    return {"reason": RATE_LIMIT, "reset_in": info['reset_in_seconds']}
                </div>
            </div>

            <!-- Exponential Backoff -->
            <div class="section">
                <h2>Exponential Backoff + Jitter</h2>

                <div class="component">
                    <h3>Параметры стратегии:</h3>
                    <ul class="feature-list">
                        <li class="feature-item">base_delay: 1 сек (начальная задержка)</li>
                        <li class="feature-item">max_delay: 30 сек (максимальная задержка)</li>
                        <li class="feature-item">max_retries: 3 попытки</li>
                        <li class="feature-item">jitter: случайный разброс ±10%</li>
                    </ul>
                </div>

                <div class="metrics">
                    <div class="metric-card">
                        <div class="metric-value">1s</div>
                        <div class="metric-label">Попытка 1</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">2s</div>
                        <div class="metric-label">Попытка 2</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">4s</div>
                        <div class="metric-label">Попытка 3</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">+10%</div>
                        <div class="metric-label">Jitter</div>
                    </div>
                </div>
            </div>

            <!-- HTTP Status Mapping -->
            <div class="section">
                <h2>Маппинг HTTP статусов → ReasonCode</h2>

                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <tr style="background: #f0f0f0;">
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">HTTP код</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">ReasonCode</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Повтор?</th>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="status-ok">200</span></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">SUCCESS</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="status-ok">Нет</span></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="status-retry">429</span></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">RATE_LIMIT</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="status-retry">Да</span></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="status-retry">500</span></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">API_ERROR</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="status-retry">Да</span></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="status-retry">503</span></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">API_ERROR</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="status-retry">Да</span></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="status-retry">504</span></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">TIMEOUT</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="status-retry">Да</span></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="status-error">400</span></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">INVALID_ORDER</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="status-error">Нет</span></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px;"><span class="status-error">404</span></td>
                        <td style="padding: 10px;">ITEM_NOT_AVAILABLE</td>
                        <td style="padding: 10px;"><span class="status-error">Нет</span></td>
                    </tr>
                </table>
            </div>

            <!-- Components -->
            <div class="section">
                <h2>Компоненты Stage 2</h2>

                <div class="component">
                    <h3>LolzteamAPIClient</h3>
                    <p>Основной асинхронный клиент для работы с API LOLZTEAM</p>
                    <ul class="feature-list">
                        <li class="feature-item">async get_product(product_id)</li>
                        <li class="feature-item">async list_products(category_id)</li>
                        <li class="feature-item">Встроенная обработка ошибок</li>
                        <li class="feature-item">Автоматические ретраи</li>
                    </ul>
                </div>

                <div class="component">
                    <h3>RateLimiter (Redis)</h3>
                    <p>Token Bucket rate limiting на основе Redis</p>
                    <ul class="feature-list">
                        <li class="feature-item">is_allowed(max_requests, window_seconds)</li>
                        <li class="feature-item">Fixed-window алгоритм</li>
                        <li class="feature-item">Счетчик оставшихся токенов</li>
                        <li class="feature-item">reset() для сброса состояния</li>
                    </ul>
                </div>

                <div class="component">
                    <h3>ExponentialBackoff</h3>
                    <p>Стратегия повторных попыток с экспоненциальной задержкой</p>
                    <ul class="feature-list">
                        <li class="feature-item">Configurable base и max delay</li>
                        <li class="feature-item">Jitter для избежания thundering herd</li>
                        <li class="feature-item">get_delay() и wait() методы</li>
                        <li class="feature-item">should_retry() для проверки</li>
                    </ul>
                </div>

                <div class="component">
                    <h3>HTTP Status Mapper</h3>
                    <p>Преобразование HTTP кодов в доменные ReasonCodes</p>
                    <ul class="feature-list">
                        <li class="feature-item">map_http_status_to_reason_code()</li>
                        <li class="feature-item">is_retryable_status() проверка</li>
                        <li class="feature-item">is_client_error() / is_server_error()</li>
                        <li class="feature-item">Консистентные коды ошибок</li>
                    </ul>
                </div>
            </div>

            <!-- Error Scenarios -->
            <div class="section">
                <h2>Сценарии обработки ошибок</h2>

                <div style="background: white; border-radius: 6px; padding: 15px; margin-bottom: 15px;">
                    <h4 style="color: #dc143c; margin-bottom: 10px;">Сценарий 1: Rate Limit</h4>
                    <p>API возвращает 429 Too Many Requests</p>
                    <p style="margin-top: 8px;">→ RateLimiter блокирует запрос → ReasonCode: RATE_LIMIT</p>
                </div>

                <div style="background: white; border-radius: 6px; padding: 15px; margin-bottom: 15px;">
                    <h4 style="color: #ffc107; margin-bottom: 10px;">Сценарий 2: Temporaray Error (5xx)</h4>
                    <p>API возвращает 500/503 Internal Server Error</p>
                    <p style="margin-top: 8px;">→ ExponentialBackoff: 1s, 2s, 4s → Успех или TIMEOUT</p>
                </div>

                <div style="background: white; border-radius: 6px; padding: 15px;">
                    <h4 style="color: #28a745; margin-bottom: 10px;">Сценарий 3: Network Error</h4>
                    <p>Потеря соединения или таймаут</p>
                    <p style="margin-top: 8px;">→ Retry с backoff → ReasonCode: NETWORK_ERROR или TIMEOUT</p>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>SuperMarket Этап 2 - Отказоустойчивый API клиент</p>
            <p>Создано: 2026-05-07 | Версия: v2.0-stage2</p>
        </div>
    </div>
</body>
</html>
'''

    # Create stage 2 folder
    stage_2_dir = Path('vizual/stage_2')
    stage_2_dir.mkdir(parents=True, exist_ok=True)

    # Write HTML file
    html_file = stage_2_dir / 'api_flow.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return str(html_file)


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("Creating Stage 2 visualization...")
    html_path = generate_html()
    print(f"Generated: {html_path}")
    print("Opening in browser...")
    webbrowser.open(f'file://{os.path.abspath(html_path)}')
    print("Done")
