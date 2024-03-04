# main.py
from flask import Flask, render_template, request
import re
import json
import os
import itertools
from math import log

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        input_text = request.form['input_text']

        # Gọi hàm dịch
        translated_text = preprocess(input_text)
        _sentence = remove_vn_accent(input_text)
        words = _sentence.split()
        results = beam_search(words, k=5)

        return render_template('index.html', translated_text=' '.join(results[0][0]))
    return render_template('index.html', translated_text=None)

# Xóa dấu tiếng Việt
def remove_vn_accent(s):
    s = re.sub('[áàảãạăắằẳẵặâấầẩẫậ]', 'a', s)
    s = re.sub('[éèẻẽẹêếềểễệ]', 'e', s)
    s = re.sub('[óòỏõọôốồổỗộơớờởỡợ]', 'o', s)
    s = re.sub('[íìỉĩị]', 'i', s)
    s = re.sub('[úùủũụưứừửữự]', 'u', s)
    s = re.sub('[ýỳỷỹỵ]', 'y', s)
    s = re.sub('đ', 'd', s)
    return s

# Tạo bộ từ điển sinh dấu câu cho các từ không dấu
map_accents = {}

for word in open('vn_syllables.txt').read().splitlines():
    word = word.lower()
    no_accent_word = remove_vn_accent(word)
    if no_accent_word not in map_accents:
        map_accents[no_accent_word] = set()
    map_accents[no_accent_word].add(word)

print(map_accents['duoc'])

# Đọc lm
lm = {}
for line in open('vn_en_nextwords.txt'):
  data = json.loads(line)
  key = data['s']
  lm[key] = data
vocab_size = len(lm)
total_word = 0
for word in lm:
  total_word += lm[word]['sum']
print(vocab_size, total_word)

lm['hiếu']

# tính xác suất dùng smoothing
def get_proba(current_word, next_word):
  if current_word not in lm:
    return 1 / total_word;
  if next_word not in lm[current_word]['next']:
    return 1 / (lm[current_word]['sum'] + vocab_size)
  return (lm[current_word]['next'][next_word] + 1) / (lm[current_word]['sum'] + vocab_size)

# def get_proba(current_word, next_word):
#   try:
#     return (lm[current_word]['next'][next_word]) / (lm[current_word]['sum'])
#   except:
#     return 1e-30

# hàm beam search
def beam_search(words, k=3):
  sequences = []
  for idx, word in enumerate(words):
    if idx == 0:
      sequences = [([x], 0.0) for x in map_accents.get(word, [word])]
    else:
      all_sequences = []
      for seq in sequences:
        for next_word in map_accents.get(word, [word]):
          current_word = seq[0][-1]
          proba = get_proba(current_word, next_word)
          # print(current_word, next_word, proba, log(proba))
          proba = log(proba)
          new_seq = seq[0].copy()
          new_seq.append(next_word)
          all_sequences.append((new_seq, seq[1] + proba))
      # print(all_sequences) 
      all_sequences = sorted(all_sequences,key=lambda x: x[1], reverse=True)
      sequences = all_sequences[:k]
  return sequences

# tiền xử lý text
def preprocess(sentence):
  sentence = sentence.lower()
  sentence = re.sub(r'[.,~`!@#$%\^&*\(\)\[\]\\|:;\'"]+', ' ', sentence)
  sentence = re.sub(r'\s+', ' ', sentence).strip()
  return sentence

# test 1 câu
sentence = "Toi dang lam viec"
sentence = preprocess(sentence)
_sentence = remove_vn_accent(sentence)
words = _sentence.split()
results = beam_search(words, k=5)
print('INP:', sentence)

print('OUT:', ' '.join(results[0][0]))
print('CMP:', ' '.join(results[0][0]) == sentence)


# test 5000 câu
k = 10 
sentences =  open("test.txt").read().splitlines();
test_size = len(sentences)
print(test_size)
correct = 0
for sent in sentences:
  try: 
    sent = preprocess(sent)
    _sent = remove_vn_accent(sent)
    words = _sent.split()
    results = beam_search(words, k)
    if ' '.join(results[0][0]) == sent:
      correct += 1
  except: 
    print("err", sent)
    break
  
  print(correct / test_size)

if __name__ == '__main__':
    app.run(debug=True)