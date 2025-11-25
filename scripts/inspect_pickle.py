import pickle, json, traceback
p = 'columnas_heartdisease.pkl'
try:
    with open(p, 'rb') as f:
        data = pickle.load(f)
    print('TYPE:', type(data))
    try:
        print('AS_JSON:', json.dumps(data, ensure_ascii=False, default=str))
    except Exception:
        print('REPR:', repr(data))
except Exception:
    traceback.print_exc()
