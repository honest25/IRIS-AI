import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/io.dart';

import 'auth_service.dart';

class WsMessage {
  final String type;
  final Map<String, dynamic> data;
  const WsMessage({required this.type, required this.data});
}

class WebSocketService extends ChangeNotifier {
  WebSocketChannel? _channel;
  StreamController<WsMessage>? _controller;
  Stream<WsMessage>? _messageStream;
  bool _connected = false;
  int _retryCount = 0;
  Timer? _reconnectTimer;

  static const String wsBaseUrl = String.fromEnvironment(
    'WS_URL',
    defaultValue: 'ws://192.168.1.100:8000/api/v1',  // Update to your server IP
  );

  bool get isConnected => _connected;
  Stream<WsMessage>? get messages => _messageStream;

  void connect(String deviceId, String token) {
    _controller?.close();
    _controller = StreamController<WsMessage>.broadcast();
    _messageStream = _controller!.stream;
    _doConnect(deviceId, token);
  }

  void _doConnect(String deviceId, String token) {
    final url = '$wsBaseUrl/ws/$deviceId?token=$token';
    try {
      _channel = IOWebSocketChannel.connect(Uri.parse(url));
      _channel!.stream.listen(
        _onMessage,
        onError: (_) => _onDisconnected(deviceId, token),
        onDone: () => _onDisconnected(deviceId, token),
      );
      _connected = true;
      _retryCount = 0;
      notifyListeners();
    } catch (e) {
      _onDisconnected(deviceId, token);
    }
  }

  void _onMessage(dynamic raw) {
    try {
      final data = jsonDecode(raw as String) as Map<String, dynamic>;
      final type = data['type'] as String? ?? 'unknown';
      final msg = WsMessage(type: type, data: data);
      _controller?.add(msg);
      notifyListeners();
    } catch (_) {}
  }

  void _onDisconnected(String deviceId, String token) {
    _connected = false;
    notifyListeners();
    // Exponential backoff
    final delay = Duration(seconds: (2 << _retryCount).clamp(2, 60));
    _retryCount = (_retryCount + 1).clamp(0, 5);
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(delay, () => _doConnect(deviceId, token));
  }

  void send(Map<String, dynamic> data) {
    if (_connected && _channel != null) {
      _channel!.sink.add(jsonEncode(data));
    }
  }

  void sendChatMessage(String content, {int? conversationId}) {
    send({
      'type': 'voice_command',
      'content': content,
      if (conversationId != null) 'conversation_id': conversationId,
    });
  }

  void sendNotification(String title, String body) {
    send({
      'type': 'notification',
      'notification': {'title': title, 'body': body, 'notification_type': 'info'},
    });
  }

  void disconnect() {
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _controller?.close();
    _connected = false;
    notifyListeners();
  }

  @override
  void dispose() {
    disconnect();
    super.dispose();
  }
}
