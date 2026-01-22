"""
修复transcode函数参数问题
"""

with open('transcode_service/web_ui.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 修复第一处 - upload_video中的transcode函数
content = content.replace(
    '''def transcode(tid, vpath, short):
            try:
                result = process_video(tid, vpath, short)
                pending_publish[tid] = result
            except Exception as e:
                pending_publish[tid] = {"error": str(e), "status": "failed"}
        threading.Thread(target=transcode, args=(task_id, video_path, is_short, is_darkweb)).start()''',
    '''def transcode(tid, vpath, short, darkweb):
            try:
                result = process_video(tid, vpath, short, darkweb)
                pending_publish[tid] = result
            except Exception as e:
                pending_publish[tid] = {"error": str(e), "status": "failed"}
        threading.Thread(target=transcode, args=(task_id, video_path, is_short, is_darkweb)).start()'''
)

# 修复第二处 - add_local_file中的transcode函数
content = content.replace(
    '''def transcode(tid, vpath, short):
        try:
            result = process_video(tid, vpath, short)
            pending_publish[tid] = result
        except Exception as e:
            pending_publish[tid] = {"error": str(e), "status": "failed"}
    threading.Thread(target=transcode, args=(task_id, video_path, is_short, is_darkweb)).start()''',
    '''def transcode(tid, vpath, short, darkweb):
        try:
            result = process_video(tid, vpath, short, darkweb)
            pending_publish[tid] = result
        except Exception as e:
            pending_publish[tid] = {"error": str(e), "status": "failed"}
    threading.Thread(target=transcode, args=(task_id, video_path, is_short, is_darkweb)).start()'''
)

with open('transcode_service/web_ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed transcode function arguments")
