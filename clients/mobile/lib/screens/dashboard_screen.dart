import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_service.dart';
import '../services/websocket_service.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _tabIndex = 0;
  final _msgCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();

  final List<Map<String, String>> _messages = [];
  bool _streaming = false;
  String _streamBuffer = '';
  int? _activeConversationId;

  @override
  void initState() {
    super.initState();
    _connectWS();
    _listenToWS();
  }

  void _connectWS() {
    final auth = context.read<AuthService>();
    final ws = context.read<WebSocketService>();
    if (auth.accessToken != null) {
      ws.connect('android-app', auth.accessToken!);
    }
  }

  void _listenToWS() {
    final ws = context.read<WebSocketService>();
    ws.messages?.listen((msg) {
      if (!mounted) return;
      switch (msg.type) {
        case 'llm_chunk':
          setState(() {
            _streamBuffer += (msg.data['content'] as String? ?? '');
          });
          _scrollToBottom();
        case 'llm_response':
          setState(() {
            _streaming = false;
            _messages.add({
              'role': 'assistant',
              'content': msg.data['content'] as String? ?? '',
            });
            _streamBuffer = '';
            if (msg.data['conversation_id'] != null) {
              _activeConversationId = msg.data['conversation_id'] as int;
            }
          });
          _scrollToBottom();
        case 'notification':
          final n = msg.data['notification'] as Map<String, dynamic>?;
          if (n != null) _showSnack(n['title'] as String? ?? 'IRIS', n['body'] as String? ?? '');
      }
    });
  }

  void _sendMessage() {
    final text = _msgCtrl.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add({'role': 'user', 'content': text});
      _streaming = true;
      _streamBuffer = '';
    });
    _msgCtrl.clear();

    final ws = context.read<WebSocketService>();
    ws.sendChatMessage(text, conversationId: _activeConversationId);
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _showSnack(String title, String body) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
            Text(body, style: const TextStyle(fontSize: 11)),
          ],
        ),
        backgroundColor: const Color(0xFF080F1A),
        shape: RoundedRectangleBorder(
          side: const BorderSide(color: Color(0xFF4AE0FF), width: 0.5),
          borderRadius: BorderRadius.circular(4),
        ),
        duration: const Duration(seconds: 4),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    const irisCyan = Color(0xFF4AE0FF);
    final auth = context.watch<AuthService>();
    final ws = context.watch<WebSocketService>();

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 8, height: 8,
              decoration: BoxDecoration(
                color: ws.isConnected ? const Color(0xFF39FF9A) : const Color(0xFFFF4A6E),
                shape: BoxShape.circle,
                boxShadow: [BoxShadow(
                  color: (ws.isConnected ? const Color(0xFF39FF9A) : const Color(0xFFFF4A6E)).withOpacity(0.8),
                  blurRadius: 6,
                )],
              ),
            ),
            const SizedBox(width: 8),
            const Text('IRIS AI'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout_rounded, size: 18),
            onPressed: () async {
              ws.disconnect();
              await auth.logout();
            },
          ),
        ],
      ),
      body: IndexedStack(
        index: _tabIndex,
        children: [
          _buildChatTab(irisCyan, auth),
          _buildStatusTab(irisCyan, ws, auth),
        ],
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: Color(0x204AE0FF))),
          color: Color(0xFF080F1A),
        ),
        child: BottomNavigationBar(
          currentIndex: _tabIndex,
          onTap: (i) => setState(() => _tabIndex = i),
          backgroundColor: Colors.transparent,
          selectedItemColor: irisCyan,
          unselectedItemColor: irisCyan.withOpacity(0.3),
          selectedLabelStyle: GoogleFonts.spaceMono(fontSize: 10),
          unselectedLabelStyle: GoogleFonts.spaceMono(fontSize: 10),
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.chat_bubble_outline), label: 'Chat'),
            BottomNavigationBarItem(icon: Icon(Icons.dashboard_outlined), label: 'Status'),
          ],
        ),
      ),
    );
  }

  Widget _buildChatTab(Color irisCyan, AuthService auth) {
    return Column(
      children: [
        Expanded(
          child: ListView.builder(
            controller: _scrollCtrl,
            padding: const EdgeInsets.all(12),
            itemCount: _messages.length + (_streaming ? 1 : 0),
            itemBuilder: (ctx, i) {
              if (i == _messages.length && _streaming) {
                return _buildBubble(
                  role: 'assistant',
                  content: _streamBuffer.isEmpty ? '...' : _streamBuffer,
                  isStreaming: true,
                );
              }
              final msg = _messages[i];
              return _buildBubble(role: msg['role']!, content: msg['content']!);
            },
          ),
        ),
        // Input
        Container(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
          decoration: const BoxDecoration(
            border: Border(top: BorderSide(color: Color(0x104AE0FF))),
          ),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _msgCtrl,
                  style: const TextStyle(color: Color(0xFF4AE0FF), fontSize: 13),
                  decoration: const InputDecoration(
                    hintText: 'Ask IRIS...',
                    isDense: true,
                    contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  ),
                  onSubmitted: (_) => _sendMessage(),
                ),
              ),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: _sendMessage,
                child: Container(
                  width: 40, height: 40,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(4),
                    color: const Color(0x264AE0FF),
                    border: Border.all(color: const Color(0x804AE0FF)),
                  ),
                  child: const Icon(Icons.send_rounded, color: Color(0xFF4AE0FF), size: 18),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildBubble({
    required String role,
    required String content,
    bool isStreaming = false,
  }) {
    final isUser = role == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        decoration: BoxDecoration(
          color: isUser
              ? const Color(0x154AE0FF)
              : const Color(0x101E90FF),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(12),
            topRight: const Radius.circular(12),
            bottomLeft: isUser ? const Radius.circular(12) : const Radius.circular(2),
            bottomRight: isUser ? const Radius.circular(2) : const Radius.circular(12),
          ),
          border: Border.all(
            color: isUser
                ? const Color(0x304AE0FF)
                : const Color(0x201E90FF),
          ),
        ),
        child: Text(
          content + (isStreaming && content != '...' ? '▋' : ''),
          style: const TextStyle(
            color: Color(0xCC4AE0FF),
            fontSize: 13,
            height: 1.5,
          ),
        ),
      ),
    );
  }

  Widget _buildStatusTab(Color irisCyan, WebSocketService ws, AuthService auth) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _statusCard('Connection', ws.isConnected ? 'ONLINE' : 'OFFLINE',
              ws.isConnected ? const Color(0xFF39FF9A) : const Color(0xFFFF4A6E)),
          const SizedBox(height: 12),
          _statusCard('User', auth.user?['email'] ?? 'Unknown', irisCyan),
          const SizedBox(height: 12),
          _statusCard('Role', (auth.user?['role'] as String? ?? 'user').toUpperCase(), irisCyan),
          const SizedBox(height: 24),
          const Text(
            'QUICK COMMANDS',
            style: TextStyle(
              color: Color(0x604AE0FF),
              fontSize: 10,
              letterSpacing: 3,
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8, runSpacing: 8,
            children: [
              _commandBtn('🔒 Lock PC', 'lock_screen', ws),
              _commandBtn('💤 Sleep PC', 'sleep', ws),
              _commandBtn('🔊 Vol Up', 'volume_up', ws),
              _commandBtn('🔉 Vol Down', 'volume_down', ws),
              _commandBtn('📸 Screenshot', 'take_screenshot', ws),
            ],
          ),
        ],
      ),
    );
  }

  Widget _statusCard(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF080F1A),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: const Color(0x204AE0FF)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Color(0x604AE0FF), fontSize: 11)),
          Text(value, style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _commandBtn(String label, String action, WebSocketService ws) {
    return GestureDetector(
      onTap: () => ws.sendChatMessage('Execute: $action'),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: const Color(0x0A4AE0FF),
          borderRadius: BorderRadius.circular(4),
          border: Border.all(color: const Color(0x304AE0FF)),
        ),
        child: Text(label, style: const TextStyle(color: Color(0xFF4AE0FF), fontSize: 11)),
      ),
    );
  }

  @override
  void dispose() {
    _msgCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }
}
