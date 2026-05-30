import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class AuthService extends ChangeNotifier {
  static const _storage = FlutterSecureStorage();
  static const String _accessKey = 'iris_access_token';
  static const String _refreshKey = 'iris_refresh_token';

  String? _accessToken;
  String? _refreshToken;
  Map<String, dynamic>? _currentUser;

  // Base URL — update to your server IP for device testing
  static const String baseUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://192.168.1.100:8000/api/v1',  // Update to your server IP
  );

  bool get isLoggedIn => _accessToken != null;
  String? get accessToken => _accessToken;
  Map<String, dynamic>? get user => _currentUser;

  Future<void> initialize() async {
    _accessToken = await _storage.read(key: _accessKey);
    _refreshToken = await _storage.read(key: _refreshKey);
    if (_accessToken != null) {
      await _fetchUser();
    }
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'username=${Uri.encodeComponent(email)}&password=${Uri.encodeComponent(password)}',
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        await _saveTokens(data['access_token'], data['refresh_token']);
        await _fetchUser();
        notifyListeners();
        return true;
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  Future<bool> register(String email, String password, String fullName) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password, 'full_name': fullName}),
      );
      return res.statusCode == 201;
    } catch (_) {
      return false;
    }
  }

  Future<void> logout() async {
    try {
      await http.post(
        Uri.parse('$baseUrl/auth/logout'),
        headers: {'Authorization': 'Bearer $_accessToken'},
      );
    } catch (_) {}
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
    _accessToken = null;
    _refreshToken = null;
    _currentUser = null;
    notifyListeners();
  }

  Future<bool> refreshTokens() async {
    if (_refreshToken == null) return false;
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/auth/refresh'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': _refreshToken}),
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        await _saveTokens(data['access_token'], data['refresh_token']);
        return true;
      }
    } catch (_) {}
    await logout();
    return false;
  }

  Future<void> _fetchUser() async {
    try {
      final res = await http.get(
        Uri.parse('$baseUrl/auth/me'),
        headers: {'Authorization': 'Bearer $_accessToken'},
      );
      if (res.statusCode == 200) {
        _currentUser = jsonDecode(res.body);
      } else if (res.statusCode == 401) {
        // Try refresh
        final refreshed = await refreshTokens();
        if (!refreshed) await logout();
      }
    } catch (_) {}
  }

  Future<void> _saveTokens(String access, String refresh) async {
    _accessToken = access;
    _refreshToken = refresh;
    await _storage.write(key: _accessKey, value: access);
    await _storage.write(key: _refreshKey, value: refresh);
  }
}
