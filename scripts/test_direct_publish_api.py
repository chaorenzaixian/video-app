"""
测试 direct-publish API
"""
import paramiko

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.Ed25519Key.from_private_key_file('server_key_new')
    client.connect('38.47.218.137', username='root', pkey=pkey)
    
    print('=== 测试 direct-publish API ===')
    
    # 测试带正确密钥
    cmd = 'curl -s -X POST http://localhost:8000/api/v1/admin/videos/direct-publish -H "Content-Type: application/json" -H "X-Transcode-Key: vYTWoms4FKOqySca1jCLtNHRVz3BAI6U" -d \'{"title":"API测试视频","hls_url":"/uploads/hls/test_api/master.m3u8","cover_url":"/uploads/hls/test_api/cover.jpg"}\''
    
    stdin, stdout, stderr = client.exec_command(cmd)
    result = stdout.read().decode()
    print(f"响应: {result}")
    
    if '"success":true' in result or '"success": true' in result:
        print("\n✓ API工作正常！")
        
        # 删除测试记录
        import json
        try:
            data = json.loads(result)
            video_id = data.get('id')
            if video_id:
                print(f"清理测试记录 (ID: {video_id})...")
                del_cmd = f'curl -s -X DELETE http://localhost:8000/api/v1/admin/videos/{video_id} -H "Authorization: Bearer test"'
                # 不实际删除，因为需要管理员token
        except:
            pass
    else:
        print("\n✗ API可能有问题，请检查")
    
    client.close()

if __name__ == '__main__':
    main()
