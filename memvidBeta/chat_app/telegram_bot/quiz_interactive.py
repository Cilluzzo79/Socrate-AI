"""
Interactive Quiz with Grading - User can answer questions and get scored
"""

import re
from pathlib import Path
import base64


def encode_logo(logo_path: str = None) -> str:
    """Encode logo to base64 or return SVG placeholder."""
    if logo_path and Path(logo_path).exists():
        try:
            with open(logo_path, 'rb') as f:
                logo_data = base64.b64encode(f.read()).decode('utf-8')
                ext = Path(logo_path).suffix.lower()
                mime_type = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.svg': 'image/svg+xml'
                }.get(ext, 'image/png')
                return f"data:{mime_type};base64,{logo_data}"
        except:
            pass

    return """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 60'%3E%3Ctext x='10' y='40' font-family='Arial Black' font-size='32' fill='%2306b6d4'%3ESocrate AI%3C/text%3E%3C/svg%3E"""


def generate_interactive_quiz_html(quiz_content: str, document_title: str, quiz_config: dict, logo_path: str = None) -> str:
    """
    Generate interactive HTML quiz where users can answer questions and get a score.

    Args:
        quiz_content: The raw quiz text from LLM
        document_title: Document name
        quiz_config: Quiz configuration dict
        logo_path: Optional path to logo

    Returns:
        str: Complete HTML with interactive quiz and grading
    """
    from telegram_bot.quiz_cards import parse_quiz_questions, escape_html

    logo_uri = encode_logo(logo_path)

    # Parse questions and answers
    questions = parse_quiz_questions(quiz_content, quiz_config.get('type', 'mixed'))
    quiz_type = quiz_config.get('type', 'mixed')

    # Generate questions HTML
    questions_html = ""
    for i, q in enumerate(questions, 1):
        questions_html += generate_question_html(i, q['question'], q['answer'], quiz_type)

    # Get labels
    quiz_type_label = {
        'multiple_choice': 'Scelta Multipla',
        'true_false': 'Vero/Falso',
        'short_answer': 'Risposta Breve',
        'mixed': 'Misto'
    }.get(quiz_type, 'Quiz')

    difficulty_label = {
        'easy': 'Facile',
        'medium': 'Medio',
        'hard': 'Difficile'
    }.get(quiz_config.get('difficulty', 'medium'), 'Medio')

    # Build answers JSON for JavaScript validation
    answers_json = "{\n"
    for i, q in enumerate(questions, 1):
        # Normalize answer for comparison
        answer = q['answer'].strip().upper()
        answers_json += f'        {i}: "{escape_js(answer)}",\n'
    answers_json += "    }"

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quiz Interattivo - {document_title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding-bottom: 100px;
        }}

        .header {{
            background: white;
            border-radius: 24px;
            padding: 40px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        }}

        .header img {{
            height: 50px;
            margin-bottom: 20px;
        }}

        .header h1 {{
            color: #667eea;
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }}

        .header-meta {{
            color: #666;
            font-size: 1.1rem;
            margin-top: 12px;
        }}

        .quiz-info {{
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}

        .quiz-info h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5rem;
            font-weight: 700;
        }}

        .quiz-info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}

        .info-item {{
            padding: 15px;
            background: #f8f9ff;
            border-radius: 12px;
            border-left: 4px solid #667eea;
        }}

        .info-label {{
            font-size: 0.85rem;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}

        .info-value {{
            font-size: 1.2rem;
            font-weight: 600;
            color: #333;
        }}

        .info-tip {{
            margin-top: 20px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            border-radius: 12px;
            border-left: 4px solid #667eea;
            font-style: italic;
            color: #555;
        }}

        .question-card {{
            background: white;
            border-radius: 20px;
            padding: 35px;
            margin-bottom: 25px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }}

        .question-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.18);
            border-color: #667eea20;
        }}

        .question-card.answered {{
            background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
        }}

        .question-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }}

        .question-number {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.3rem;
            margin-right: 15px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }}

        .question-text {{
            font-size: 1.15rem;
            font-weight: 600;
            color: #2d3748;
            line-height: 1.8;
            white-space: pre-wrap;
            flex: 1;
        }}

        .answer-options {{
            margin-top: 25px;
        }}

        .radio-option {{
            display: flex;
            align-items: center;
            padding: 18px 22px;
            margin-bottom: 12px;
            background: #f7fafc;
            border: 2px solid #e2e8f0;
            border-radius: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
        }}

        .radio-option:hover {{
            background: #edf2f7;
            border-color: #cbd5e0;
            transform: translateX(5px);
        }}

        .radio-option input[type="radio"] {{
            width: 24px;
            height: 24px;
            margin-right: 15px;
            cursor: pointer;
            accent-color: #667eea;
        }}

        .radio-option label {{
            font-size: 1.05rem;
            font-weight: 500;
            color: #2d3748;
            cursor: pointer;
            flex: 1;
        }}

        .radio-option.selected {{
            background: #667eea10;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}

        .radio-option.correct {{
            background: #10b98115;
            border-color: #10b981;
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
        }}

        .radio-option.incorrect {{
            background: #ef444415;
            border-color: #ef4444;
            box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
        }}

        .correct-answer-box {{
            display: none;
            margin-top: 20px;
            padding: 18px 22px;
            background: linear-gradient(135deg, #10b98108 0%, #10b98115 100%);
            border-left: 5px solid #10b981;
            border-radius: 12px;
            color: #065f46;
            font-weight: 500;
        }}

        .submit-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 18px 40px;
            border-radius: 60px;
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .submit-btn:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(102, 126, 234, 0.5);
        }}

        .submit-btn:active {{
            transform: translateY(-2px);
        }}

        .results-modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.75);
            backdrop-filter: blur(8px);
            z-index: 2000;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .results-content {{
            background: white;
            border-radius: 30px;
            padding: 50px;
            max-width: 550px;
            text-align: center;
            box-shadow: 0 25px 80px rgba(0,0,0,0.4);
            animation: slideUp 0.4s ease;
        }}

        @keyframes slideUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .results-content h2 {{
            color: #667eea;
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 25px;
        }}

        .score-display {{
            font-size: 5rem;
            font-weight: 900;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 25px 0;
            text-shadow: 0 0 20px rgba(102, 126, 234, 0.2);
        }}

        .score-message {{
            font-size: 1.25rem;
            color: #555;
            margin-bottom: 35px;
            line-height: 1.6;
        }}

        .close-btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 16px 40px;
            border-radius: 30px;
            font-size: 1.05rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
        }}

        .close-btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }}

        @media print {{
            body {{
                background: white;
            }}
            .submit-btn {{
                display: none !important;
            }}
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8rem;
            }}
            .question-text {{
                font-size: 1rem;
            }}
            .submit-btn {{
                bottom: 20px;
                right: 20px;
                padding: 14px 30px;
                font-size: 1rem;
            }}
            .results-content {{
                padding: 35px 25px;
                margin: 20px;
            }}
            .score-display {{
                font-size: 3.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="{logo_uri}" alt="Logo">
            <h1>🎯 Quiz Interattivo</h1>
            <div class="header-meta">
                <strong>{document_title}</strong>
            </div>
        </div>

        <div class="quiz-info">
            <h2>📊 Informazioni Quiz</h2>
            <div class="quiz-info-grid">
                <div class="info-item">
                    <div class="info-label">Tipo</div>
                    <div class="info-value">{quiz_type_label}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Difficoltà</div>
                    <div class="info-value">{difficulty_label}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Domande</div>
                    <div class="info-value">{len(questions)}</div>
                </div>
            </div>
            <div class="info-tip">
                💡 <strong>Suggerimento:</strong> Rispondi a tutte le domande selezionando l'opzione corretta, poi clicca "Valuta Quiz" per vedere il tuo punteggio e le risposte corrette!
            </div>
        </div>

        <div id="questions-container">
            {questions_html}
        </div>
    </div>

    <button class="submit-btn" onclick="gradeQuiz()">
        <span>✅</span>
        <span>Valuta Quiz</span>
    </button>

    <div class="results-modal" id="results-modal">
        <div class="results-content">
            <h2>🎉 Risultati</h2>
            <div class="score-display" id="score-display">0%</div>
            <div class="score-message" id="score-message"></div>
            <button class="close-btn" onclick="closeResults()">Chiudi</button>
        </div>
    </div>

    <script>
        const correctAnswers = {answers_json};
        const quizType = "{quiz_type}";

        // Track selected answers
        document.querySelectorAll('input[type="radio"]').forEach(radio => {{
            radio.addEventListener('change', function() {{
                // Mark card as answered
                const card = this.closest('.question-card');
                card.classList.add('answered');

                // Highlight selected option
                const allOptions = card.querySelectorAll('.radio-option');
                allOptions.forEach(opt => opt.classList.remove('selected'));
                this.closest('.radio-option').classList.add('selected');
            }});
        }});

        function normalizeAnswer(answer) {{
            return answer.trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
        }}

        function getSelectedAnswer(questionNum) {{
            const selected = document.querySelector(`input[name="q${{questionNum}}"]:checked`);
            return selected ? selected.value : '';
        }}

        function gradeQuiz() {{
            let correct = 0;
            let total = Object.keys(correctAnswers).length;
            let allAnswered = true;

            for (let i = 1; i <= total; i++) {{
                const userAnswer = getSelectedAnswer(i);

                if (!userAnswer) {{
                    allAnswered = false;
                    continue;
                }}

                const correctAnswerDiv = document.getElementById('correct-' + i);
                const card = document.getElementById('card-' + i);
                const userOption = document.querySelector(`input[name="q${{i}}"]:checked`).closest('.radio-option');
                const correctAnswer = normalizeAnswer(correctAnswers[i]);
                const normalizedUser = normalizeAnswer(userAnswer);

                if (normalizedUser === correctAnswer) {{
                    correct++;
                    userOption.classList.add('correct');
                    correctAnswerDiv.style.display = 'none';
                }} else {{
                    userOption.classList.add('incorrect');
                    correctAnswerDiv.style.display = 'block';

                    // Highlight the correct answer
                    const correctOption = card.querySelector(`input[value="${{correctAnswers[i]}}"]`);
                    if (correctOption) {{
                        correctOption.closest('.radio-option').classList.add('correct');
                    }}
                }}
            }}

            if (!allAnswered) {{
                alert('⚠️ Per favore, rispondi a tutte le domande prima di valutare!');
                return;
            }}

            const percentage = Math.round((correct / total) * 100);
            const scoreDisplay = document.getElementById('score-display');
            const scoreMessage = document.getElementById('score-message');
            const modal = document.getElementById('results-modal');

            scoreDisplay.textContent = percentage + '%';

            let message = '';
            let emoji = '';
            if (percentage === 100) {{
                emoji = '🏆';
                message = '<strong>Perfetto!</strong> Hai risposto correttamente a tutte le domande!';
            }} else if (percentage >= 80) {{
                emoji = '🎉';
                message = '<strong>Ottimo lavoro!</strong> Hai una buona comprensione dell\\'argomento.';
            }} else if (percentage >= 60) {{
                emoji = '👍';
                message = '<strong>Buon risultato!</strong> Continua a studiare per migliorare.';
            }} else if (percentage >= 40) {{
                emoji = '📚';
                message = '<strong>Devi ancora ripassare un po\\'.</strong> Rileggi il materiale!';
            }} else {{
                emoji = '💪';
                message = '<strong>Non scoraggiarti!</strong> Rivedi l\\'argomento e riprova.';
            }}

            message = emoji + ' ' + message + `<br><br>Hai risposto correttamente a <strong>${{correct}} su ${{total}}</strong> domande.`;
            scoreMessage.innerHTML = message;

            modal.style.display = 'flex';
        }}

        function closeResults() {{
            document.getElementById('results-modal').style.display = 'none';
        }}

        // Allow Ctrl+Enter to submit
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Enter' && e.ctrlKey) {{
                gradeQuiz();
            }}
        }});
    </script>
</body>
</html>"""


def generate_question_html(number: int, question: str, answer: str, quiz_type: str) -> str:
    """Generate HTML for a single question with appropriate input type."""
    from telegram_bot.quiz_cards import escape_html

    # For true/false questions, use radio buttons
    if quiz_type == 'true_false':
        return f"""
    <div class="question-card" id="card-{number}">
        <div class="question-header">
            <div class="question-number">{number}</div>
            <div class="question-text">{escape_html(question)}</div>
        </div>
        <div class="answer-options">
            <label class="radio-option">
                <input type="radio" name="q{number}" value="VERO" id="q{number}-vero">
                <label for="q{number}-vero">✓ Vero</label>
            </label>
            <label class="radio-option">
                <input type="radio" name="q{number}" value="FALSO" id="q{number}-falso">
                <label for="q{number}-falso">✗ Falso</label>
            </label>
        </div>
        <div class="correct-answer-box" id="correct-{number}">
            <strong>✅ Risposta corretta:</strong> {escape_html(answer)}
        </div>
    </div>"""
    else:
        # For other types, use text input (can be extended for multiple choice)
        return f"""
    <div class="question-card" id="card-{number}">
        <div class="question-header">
            <div class="question-number">{number}</div>
            <div class="question-text">{escape_html(question)}</div>
        </div>
        <div class="answer-options">
            <input type="text" id="answer-{number}" name="q{number}" class="answer-input" placeholder="Inserisci la tua risposta..." style="width: 100%; padding: 15px; font-size: 1rem; border: 2px solid #e2e8f0; border-radius: 12px;">
        </div>
        <div class="correct-answer-box" id="correct-{number}">
            <strong>✅ Risposta corretta:</strong> {escape_html(answer)}
        </div>
    </div>"""


def escape_js(text: str) -> str:
    """Escape text for JavaScript strings."""
    return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', '')
