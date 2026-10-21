from google import genai
import os
from dotenv import load_dotenv
import time
import csv
from datetime import datetime
from zoneinfo import ZoneInfo

from src import config

gemini_api_path = config.BACKEND_DIR / '.env'

THINK_LEVEL = ['low', 'medium', 'high']
MODEL = 'gemini-4-argon'
MAX_OUTPUT_TOKENS = 8192
N_RUNS = 3
SEED = 42
INPUT_PRICE_PER_M = 2.00 # USD / 100万トークン(11/30まで)
OUTPUT_PRICE_PER_M = 10.00 # 思考込み
SYSTEM_PROMPT = 'あなたは優秀な法的アシスタントです。ユーザーからの質問に対して、関連する法令や制度を踏まえ、正確かつ分かりやすい日本語で回答してください。'
prompt = "訪問販売で契約した場合、クーリング・オフは何日以内にできますか。"

load_dotenv(gemini_api_path)

GEMINI_API_KEY = os.getenv('GEMINI_BENCH_API_KEY')

if GEMINI_API_KEY is None:
    raise ValueError('APIキーを見つけられませんでした')

client = genai.Client(api_key=GEMINI_API_KEY)

header = [
    'Model', 'Thinking Level', 'Run', 'TTFO(s)', 'Latency(s)', 'TPOT(ms)', 'Speed(tok/s)', 'Input Tokens', 'Think Tokens', 'Answer Tokens',
    'Generated Tokens', 'Max Output Tokens', 'Hit Limit', 'Cost(USD)', 'Correct', 'Answer Text', 'Error',
]

today_str = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d")
file_name = "Gemini-4-Argon_Benchmark" + "_" + today_str + ".csv"
with open(file_name, 'w', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(header)

warm_up_prompt = '日本の首都はどこですか？'
# ウォームアップ
_ = client.interactions.create(
    model=MODEL,
    input=warm_up_prompt,
    generation_config={
        'thinking_level': 'low',
        'max_output_tokens': 128,
    },
)

def measure_once(thinking_level):
    ttfo = None
    latency = None
    usage = None
    answer_parts = []
    
    start = time.perf_counter()
    
    stream = client.interactions.create(
        model=MODEL,
        system_instruction=SYSTEM_PROMPT,
        input=prompt,
        generation_config={
            'thinking_level': thinking_level,
            'max_output_tokens': MAX_OUTPUT_TOKENS,
            'seed': SEED,
        },
        stream=True,
    )
    
    for event in stream:
        now = time.perf_counter()
        if event.event_type == 'step.delta' and event.delta.type == 'text':
            if ttfo is None:
                ttfo = now - start
            answer_parts.append(event.delta.text)
            print(event.delta.text, end='', flush=True)
        elif event.event_type == 'interaction.completed':
            latency = now - start
            usage = event.interaction.usage
        elif event.event_type == 'error':
            raise RuntimeError(f'ストリーム中にエラー: {event}')
    print()
    if usage is None:
        raise RuntimeError('interaction.completed が届きませんでした')
    answer_text = ''.join(answer_parts)
    return ttfo, latency, usage, answer_text


for thinking_level in THINK_LEVEL:
    for run in range(1, N_RUNS + 1):
        print(f'{thinking_level} {run}回目')
        try:
            ttfo, latency, usage, answer_text = measure_once(thinking_level)
        except Exception as e:
            error_message = f'ERROR: {type(e).__name__}: {e}'
            error_row = [
                MODEL, thinking_level, run,
                '', '', '', '', '', '', '', '', MAX_OUTPUT_TOKENS, '', '', '', '',
                error_message,
            ]
            with open(file_name, 'a', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(error_row)
            print(error_row)
            continue
        input_tokens = usage.total_input_tokens
        think_tokens = usage.total_thought_tokens
        answer_tokens = usage.total_output_tokens
        generate_tokens = think_tokens + answer_tokens
        if ttfo is None:
            ttfo_value = ''
            tpot = 0.0
        elif answer_tokens > 1:
            ttfo_value = round(ttfo, 2)
            tpot = (latency - ttfo) / (answer_tokens - 1) * 1000
        else:
            ttfo_value = round(ttfo, 2)
            tpot = 0.0
        speed = generate_tokens / latency
        hit_limit = generate_tokens >= MAX_OUTPUT_TOKENS
        input_cost = input_tokens * INPUT_PRICE_PER_M
        output_cost = generate_tokens * OUTPUT_PRICE_PER_M
        cost = (input_cost + output_cost) / 1000000
        correct = '8日' in answer_text
        row = [
            MODEL, thinking_level, run, ttfo_value, round(latency, 2), round(tpot, 1), round(speed, 1), input_tokens, think_tokens, answer_tokens,
            generate_tokens, MAX_OUTPUT_TOKENS, hit_limit, round(cost, 6), correct, answer_text, ''
        ]
        with open(file_name, 'a', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(row)
