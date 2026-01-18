/// JS Bridge 消息模型 - 用于 Flutter 和 WebView 之间的通信
class JSBridgeMessage {
  final String action;
  final Map<String, dynamic>? data;

  JSBridgeMessage({
    required this.action,
    this.data,
  });

  factory JSBridgeMessage.fromJson(Map<String, dynamic> json) {
    return JSBridgeMessage(
      action: json['action'] as String,
      data: json['data'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() => {
    'action': action,
    if (data != null) 'data': data,
  };

  @override
  String toString() => 'JSBridgeMessage(action: $action, data: $data)';

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is JSBridgeMessage &&
        other.action == action &&
        _mapEquals(other.data, data);
  }

  @override
  int get hashCode => action.hashCode ^ (data?.hashCode ?? 0);

  static bool _mapEquals(Map<String, dynamic>? a, Map<String, dynamic>? b) {
    if (a == null && b == null) return true;
    if (a == null || b == null) return false;
    if (a.length != b.length) return false;
    for (final key in a.keys) {
      if (!b.containsKey(key) || a[key] != b[key]) return false;
    }
    return true;
  }
}
