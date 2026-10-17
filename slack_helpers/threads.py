def reply_in_thread(say, message, text, **kwargs):
    """届いたメッセージのスレッドに返信する。

    - スレッドの中の発言なら、そのスレッドに返す
    - チャンネル直下の発言なら、その発言を起点に新しいスレッドを作って返す

    message には、メッセージイベントやメンションイベントの中身（リスナー引数の
    message / event）を渡す。kwargs は say にそのまま渡す（blocks など）。
    """
    thread_ts = message.get("thread_ts", message["ts"])
    return say(text=text, thread_ts=thread_ts, **kwargs)
