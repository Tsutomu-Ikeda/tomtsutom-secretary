import flask
import json
import requests

app = flask.Flask(__name__)

@app.route('/', methods=['get', 'post'])
def root():
    app.logger.info(flask.request.headers)
    return 'ok'

@app.route('/interactive-hook', methods=['get', 'post'])
def slack_interactive():
    data = json.loads(flask.request.form["payload"])
    response_url = data["response_url"]
    original_message = data.get("message")
    actions = data.get("actions")

    def get_target_block(message):
        for block in message.get("blocks"):
            if block.get("type") == "actions":
                return block
        
        return None

    if (target_block := get_target_block(original_message)) is None:
        return 'ok'

    def get_list_pressed_index(values):
        return [
            i
            for i, opt
            in enumerate(target_block["elements"][0]["options"])
            if opt['value'] in values
        ]

    if len(actions[0]['selected_options']) == 0:
        return 'ok'

    list_pressed_index = get_list_pressed_index(
        [
            opt['value']
            for opt
            in actions[0]['selected_options']
        ]
    )
    if list_pressed_index:
        for i in list_pressed_index:
            del target_block["elements"][0]["options"][i]

    if len(target_block['elements'][0]['options']) == 0:
        target_block["type"] = "section"
        target_block["text"] = {
            "type": "mrkdwn",
            "text": "all done!"
        }
        del target_block["elements"]

    res = requests.post(
        response_url,
        json.dumps({
            "replace_original": True,
            "blocks": original_message.get("blocks")
        }),
        headers={'Content-Type': 'application/json'}
    )
    app.logger.info(res.text)
    return 'ok'

@app.route('/.well-known/acme-challenge/<path:filename>', methods=['get'])
def acme_challenge(filename):
    return flask.send_from_directory('/var/www/letsencrypt-webroot', filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=8080, host='0.0.0.0')
