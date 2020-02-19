from rnnmorph.predictor import RNNMorphPredictor
from pprint import pprint

if __name__ == '__main__':
    pr = RNNMorphPredictor(language='ru')
    forms = pr.predict(words=['мама', 'мыла', 'раму'])
    for i in forms:
        print('{:<15} {:<10} {}'.format(i.normal_form, i.pos, i.tag))

    forms = pr.predict_sentences(sentences=[['Всем', 'привет']])
    for i in forms[0]:
        print('{:<15} {:<10} {}'.format(i.normal_form, i.pos, i.tag))

    pprint(forms)
