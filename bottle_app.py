import jinja2
import json
import os
import tempfile

from bottle import default_app, request, route, run, static_file

import generate as gen


def _default_context(filename):
    """Returns a default context dict"""
    with open(filename) as f:
        try:
            return json.loads(f.read())
        except:
            return {}

TEMPLATE_MAP = {
        "Trvalý pobyt: Žádost o uplatnění opatření proti nečinnosti": {
            "template": "zadost_o_uplatneni_opatreni_proti_necinnosti_spravniho_organu.docx",
            "context": "necinnost_trvaly_context"},
        "Žádost o přidělení rodného čísla": {
            "template": "zadost_rodne_cislo.docx",
            "context": "rodne_cislo_context"},
        "Potvrzení o pobytu (tzv. historie pobytu)": {
            "template": "zadost_o_potvrzeni_o_pobytu.docx",
            "context": "historie_pobytu_context"}
        }
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader('./views'),
    extensions=['jinja2.ext.i18n']
)


def docform(context):
    template = env.get_or_select_template('docform.tpl')
    system_context = {}
    context_to_pass = {}
    for key, value in context.items():
        if key.startswith('__'):
            system_context[key] = value
        else:
            # check if specific type of input is required, if no given it will be text
            elem = { 'value': value }
            radio = '__{}_radio'.format(key)
            date = '__{}_date'.format(key)

            if radio in context:
                elem['input'] = 'radio'
                elem['ids'] = context[radio]
            elif date in context:
                elem['input'] = 'date'
            else:
                elem['input'] = 'text'
            context_to_pass[key] = elem

    return template.render(context=context_to_pass,
                           name=context.get('__name__', "Application"),
                           system_context=system_context)


@route('/')
def index():
    template = env.get_or_select_template('index.tpl')
    return template.render()


@route('/necinnost_trvaly_pobyt')
def necinnost_trvaly_pobyt():
    context = _default_context('necinnost_trvaly_context')
    return docform(context)


@route('/rodne_cislo_application')
def necinnost_trvaly_pobyt():
    context = _default_context('rodne_cislo_context')
    return docform(context)


@route('/historie_pobytu')
def necinnost_trvaly_pobyt():
    context = _default_context('historie_pobytu_context')
    return docform(context)


@route('/generate', method="POST")
def generate():
    data = request.forms
    docx_template_name = TEMPLATE_MAP.get(data.get('__form__'), {}).get('template')
    default_context_name = TEMPLATE_MAP.get(data.get('__form__'), {}).get('context')
    if not docx_template_name or not default_context_name:
        return
    default_context = _default_context(default_context_name)
    # vet against default context keys
    user_input_vetted = {k: v for k, v in data.iteritems() if k in default_context and v}
    context = dict(default_context)
    context.update(user_input_vetted)
    with tempfile.NamedTemporaryFile(dir="generated", delete=True) as temp_doc:
        gen.generate_doc(docx_template_name, context, temp_doc.name)
        return static_file(
                temp_doc.name.rsplit(os.path.sep)[-1],
                root="generated/",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                download=docx_template_name)

app = default_app()

if __name__ == '__main__':
    run(app, host='localhost', port=8080)
