# api_server.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import random

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 加载数据
try:
    fill_df = pd.read_csv('fill_questions.csv')
    choice_df = pd.read_csv('choice_questions.csv')
    judge_df = pd.read_csv('judge_questions.csv')
    program_df = pd.read_csv('program_questions.csv')


    # 将选项从字符串转换为字典
    def parse_options(options_str):
        if isinstance(options_str, str):
            try:
                # 尝试从字符串解析字典
                import ast
                return ast.literal_eval(options_str)
            except:
                # 如果解析失败，返回原始字符串
                return options_str
        return options_str


    choice_df['options'] = choice_df['options'].apply(parse_options)

except Exception as e:
    print(f"加载数据失败: {e}")
    fill_df = pd.DataFrame()
    choice_df = pd.DataFrame()
    judge_df = pd.DataFrame()
    program_df = pd.DataFrame()


@app.route('/api/questions/fill', methods=['GET'])
def get_fill_questions():
    """获取填空题"""
    try:
        data = fill_df.to_dict('records')
        return jsonify({
            'success': True,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/questions/choice', methods=['GET'])
def get_choice_questions():
    """获取选择题"""
    try:
        data = choice_df.to_dict('records')
        return jsonify({
            'success': True,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/questions/judge', methods=['GET'])
def get_judge_questions():
    """获取判断题"""
    try:
        data = judge_df.to_dict('records')
        return jsonify({
            'success': True,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/questions/program', methods=['GET'])
def get_program_questions():
    """获取编程题"""
    try:
        data = program_df.to_dict('records')
        return jsonify({
            'success': True,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/questions/random', methods=['GET'])
def get_random_question():
    """获取随机题目"""
    try:
        q_type = request.args.get('type', 'all')

        all_questions = []
        if q_type in ['all', 'fill'] and not fill_df.empty:
            all_questions.extend([{**q, 'type': 'fill'} for q in fill_df.to_dict('records')])
        if q_type in ['all', 'choice'] and not choice_df.empty:
            all_questions.extend([{**q, 'type': 'choice'} for q in choice_df.to_dict('records')])
        if q_type in ['all', 'judge'] and not judge_df.empty:
            all_questions.extend([{**q, 'type': 'judge'} for q in judge_df.to_dict('records')])
        if q_type in ['all', 'program'] and not program_df.empty:
            all_questions.extend([{**q, 'type': 'program'} for q in program_df.to_dict('records')])

        if not all_questions:
            return jsonify({'success': False, 'error': '没有可用的题目'}), 404

        random_question = random.choice(all_questions)
        return jsonify({
            'success': True,
            'data': random_question
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/questions/all', methods=['GET'])
def get_all_questions():
    """获取所有题目"""
    try:
        all_data = {
            'fill': fill_df.to_dict('records') if not fill_df.empty else [],
            'choice': choice_df.to_dict('records') if not choice_df.empty else [],
            'judge': judge_df.to_dict('records') if not judge_df.empty else [],
            'program': program_df.to_dict('records') if not program_df.empty else []
        }

        total = sum(len(v) for v in all_data.values())

        return jsonify({
            'success': True,
            'total': total,
            'counts': {
                'fill': len(all_data['fill']),
                'choice': len(all_data['choice']),
                'judge': len(all_data['judge']),
                'program': len(all_data['program'])
            },
            'data': all_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/questions/check-answer', methods=['POST'])
def check_answer():
    """检查答案"""
    try:
        data = request.json
        q_id = data.get('id')
        q_type = data.get('type')
        user_answer = data.get('answer')

        # 根据类型查找正确答案
        if q_type == 'fill':
            correct_row = fill_df[fill_df['id'] == q_id]
        elif q_type == 'choice':
            correct_row = choice_df[choice_df['id'] == q_id]
        elif q_type == 'judge':
            correct_row = judge_df[judge_df['id'] == q_id]
        elif q_type == 'program':
            correct_row = program_df[program_df['id'] == q_id]
        else:
            return jsonify({'success': False, 'error': '无效的题目类型'}), 400

        if correct_row.empty:
            return jsonify({'success': False, 'error': '题目不存在'}), 404

        correct_answer = correct_row.iloc[0]['answer']

        # 检查答案是否正确
        is_correct = False
        if q_type == 'fill':
            # 填空题可能有多个答案，检查用户答案是否包含在正确答案中
            if isinstance(correct_answer, str):
                correct_answer = [correct_answer]
            user_answer_str = str(user_answer).strip().lower()
            correct_answers = [str(ans).strip().lower() for ans in correct_answer]
            is_correct = user_answer_str in correct_answers
        elif q_type == 'choice':
            is_correct = str(user_answer).strip().upper() == str(correct_answer).strip().upper()
        elif q_type == 'judge':
            is_correct = str(user_answer).strip() == str(correct_answer).strip()
        elif q_type == 'program':
            # 编程题通常不自动检查，返回参考答案
            is_correct = True  # 编程题默认正确

        return jsonify({
            'success': True,
            'is_correct': is_correct,
            'correct_answer': str(correct_answer),
            'explanation': correct_row.iloc[0].get('explanation', '')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    try:
        return jsonify({
            'success': True,
            'stats': {
                'fill_count': len(fill_df) if not fill_df.empty else 0,
                'choice_count': len(choice_df) if not choice_df.empty else 0,
                'judge_count': len(judge_df) if not judge_df.empty else 0,
                'program_count': len(program_df) if not program_df.empty else 0,
                'total': (len(fill_df) if not fill_df.empty else 0) +
                         (len(choice_df) if not choice_df.empty else 0) +
                         (len(judge_df) if not judge_df.empty else 0) +
                         (len(program_df) if not program_df.empty else 0)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("数据统计:")
    print(f"填空题: {len(fill_df) if not fill_df.empty else 0} 道")
    print(f"选择题: {len(choice_df) if not choice_df.empty else 0} 道")
    print(f"判断题: {len(judge_df) if not judge_df.empty else 0} 道")
    print(f"编程题: {len(program_df) if not program_df.empty else 0} 道")
    print("\nAPI服务器启动中...")
    print("访问 http://127.0.0.1:5000 查看API端点")
    app.run(debug=True, port=5000)