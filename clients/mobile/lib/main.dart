import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import 'services/auth_service.dart';
import 'services/websocket_service.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const IrisApp());
}

class IrisApp extends StatelessWidget {
  const IrisApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthService()),
        ChangeNotifierProvider(create: (_) => WebSocketService()),
      ],
      child: MaterialApp(
        title: 'IRIS AI',
        debugShowCheckedModeBanner: false,
        theme: _buildTheme(),
        home: const AppEntry(),
      ),
    );
  }

  ThemeData _buildTheme() {
    const irisBackground = Color(0xFF050A12);
    const irisCyan = Color(0xFF4AE0FF);
    const irisBlue = Color(0xFF1E90FF);

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: irisBackground,
      colorScheme: const ColorScheme.dark(
        primary: irisCyan,
        secondary: irisBlue,
        surface: Color(0xFF080F1A),
        background: irisBackground,
      ),
      textTheme: GoogleFonts.spaceMonoTextTheme(ThemeData.dark().textTheme),
      appBarTheme: AppBarTheme(
        backgroundColor: const Color(0xFF080F1A),
        elevation: 0,
        titleTextStyle: GoogleFonts.orbitron(
          color: irisCyan,
          fontSize: 16,
          fontWeight: FontWeight.w700,
          letterSpacing: 2,
        ),
        iconTheme: const IconThemeData(color: irisCyan),
      ),
      inputDecorationTheme: InputDecorationTheme(
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(4),
          borderSide: const BorderSide(color: Color(0x304AE0FF)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(4),
          borderSide: const BorderSide(color: Color(0x304AE0FF)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(4),
          borderSide: const BorderSide(color: irisCyan),
        ),
        labelStyle: const TextStyle(color: Color(0x804AE0FF)),
        hintStyle: const TextStyle(color: Color(0x404AE0FF)),
        filled: true,
        fillColor: const Color(0x0A4AE0FF),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0x264AE0FF),
          foregroundColor: irisCyan,
          side: const BorderSide(color: Color(0x804AE0FF)),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
          textStyle: GoogleFonts.spaceMono(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            letterSpacing: 2,
          ),
        ),
      ),
    );
  }
}

class AppEntry extends StatefulWidget {
  const AppEntry({super.key});

  @override
  State<AppEntry> createState() => _AppEntryState();
}

class _AppEntryState extends State<AppEntry> {
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    final auth = context.read<AuthService>();
    await auth.initialize();
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(color: Color(0xFF4AE0FF)),
        ),
      );
    }
    final auth = context.watch<AuthService>();
    return auth.isLoggedIn ? const DashboardScreen() : const LoginScreen();
  }
}
