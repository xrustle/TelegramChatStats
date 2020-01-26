from rnnmorph.predictor import RNNMorphPredictor

pr = RNNMorphPredictor(language='ru')

if __name__ == '__main__':
    forms = pr.predict(words=['мама', 'мыла', 'раму'])
    for i in forms:
        print('{:<15} {:<10} {}'.format(i.normal_form, i.pos, i.tag))

    forms = pr.predict_sentences(sentences=[['мама', 'мыла', 'раму']])
    for i in forms[1]:
        print('{:<15} {:<10} {}'.format(i.normal_form, i.pos, i.tag))
