import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../services/auth_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _nameCtrl = TextEditingController();
  bool _isRegister = false;
  bool _loading = false;
  String _error = '';
  late AnimationController _pulseCtrl;
  late Animation<double> _pulseAnim;

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat(reverse: true);
    _pulseAnim = Tween<double>(begin: 0.85, end: 1.0).animate(
      CurvedAnimation(parent: _pulseCtrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    _nameCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() { _loading = true; _error = ''; });

    final auth = context.read<AuthService>();
    bool success;

    if (_isRegister) {
      success = await auth.register(
        _emailCtrl.text.trim(),
        _passwordCtrl.text,
        _nameCtrl.text.trim(),
      );
      if (success && mounted) {
        setState(() { _isRegister = false; _error = 'Account created. Please log in.'; });
      }
    } else {
      success = await auth.login(
        _emailCtrl.text.trim(),
        _passwordCtrl.text,
      );
    }

    if (!success && mounted) {
      setState(() => _error = _isRegister ? 'Registration failed' : 'Invalid email or password');
    }
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    const irisCyan = Color(0xFF4AE0FF);

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            center: Alignment(0, -0.3),
            radius: 1.2,
            colors: [Color(0xFF080F1A), Color(0xFF050A12)],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // ── Orb ──────────────────────────────────────────────────
                  ScaleTransition(
                    scale: _pulseAnim,
                    child: Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: const RadialGradient(
                          colors: [
                            Color(0xCCFFFFFF),
                            irisCyan,
                            Color(0x221E90FF),
                          ],
                          stops: [0.0, 0.3, 1.0],
                        ),
                        boxShadow: [
                          BoxShadow(color: irisCyan.withOpacity(0.6), blurRadius: 30),
                          BoxShadow(color: irisCyan.withOpacity(0.3), blurRadius: 60),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  // ── Title ────────────────────────────────────────────────
                  Text(
                    'IRIS',
                    style: GoogleFonts.orbitron(
                      color: irisCyan,
                      fontSize: 32,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 8,
                      shadows: [Shadow(color: irisCyan.withOpacity(0.7), blurRadius: 15)],
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'INTELLIGENT RESPONSIVE INTEGRATED SYSTEM',
                    style: GoogleFonts.spaceMono(
                      color: irisCyan.withOpacity(0.35),
                      fontSize: 7,
                      letterSpacing: 2,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 48),

                  // ── Form Card ────────────────────────────────────────────
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: const Color(0xFF080F1A).withOpacity(0.85),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: irisCyan.withOpacity(0.18)),
                      boxShadow: [
                        BoxShadow(color: irisCyan.withOpacity(0.05), blurRadius: 30),
                      ],
                    ),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        children: [
                          // Mode tabs
                          Row(
                            children: [
                              for (final (label, isReg) in [
                                ('[ AUTHENTICATE ]', false),
                                ('[ REGISTER ]', true),
                              ])
                                Expanded(
                                  child: GestureDetector(
                                    onTap: () => setState(() { _isRegister = isReg; _error = ''; }),
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(vertical: 8),
                                      decoration: BoxDecoration(
                                        border: Border(
                                          bottom: BorderSide(
                                            color: _isRegister == isReg ? irisCyan : Colors.transparent,
                                            width: 1.5,
                                          ),
                                        ),
                                      ),
                                      child: Text(
                                        label,
                                        textAlign: TextAlign.center,
                                        style: GoogleFonts.spaceMono(
                                          color: _isRegister == isReg
                                              ? irisCyan
                                              : irisCyan.withOpacity(0.3),
                                          fontSize: 10,
                                          letterSpacing: 1,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                            ],
                          ),
                          const SizedBox(height: 24),

                          if (_isRegister) ...[
                            TextFormField(
                              controller: _nameCtrl,
                              style: const TextStyle(color: Color(0xFF4AE0FF), fontSize: 13),
                              decoration: const InputDecoration(
                                labelText: 'Full Name',
                                hintText: 'Your name',
                              ),
                            ),
                            const SizedBox(height: 16),
                          ],

                          TextFormField(
                            controller: _emailCtrl,
                            keyboardType: TextInputType.emailAddress,
                            style: const TextStyle(color: Color(0xFF4AE0FF), fontSize: 13),
                            decoration: const InputDecoration(
                              labelText: 'Email',
                              hintText: 'user@domain.com',
                            ),
                            validator: (v) => v!.contains('@') ? null : 'Enter valid email',
                          ),
                          const SizedBox(height: 16),

                          TextFormField(
                            controller: _passwordCtrl,
                            obscureText: true,
                            style: const TextStyle(color: Color(0xFF4AE0FF), fontSize: 13),
                            decoration: const InputDecoration(
                              labelText: 'Password',
                              hintText: '••••••••',
                            ),
                            validator: (v) => v!.length >= 6 ? null : 'Min 6 characters',
                          ),
                          const SizedBox(height: 8),

                          if (_error.isNotEmpty) ...[
                            const SizedBox(height: 8),
                            Text(
                              _error,
                              style: TextStyle(
                                color: _error.contains('created')
                                    ? const Color(0xFF39FF9A)
                                    : const Color(0xFFFF4A6E),
                                fontSize: 11,
                                fontFamily: 'SpaceMono',
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ],

                          const SizedBox(height: 20),
                          SizedBox(
                            width: double.infinity,
                            height: 44,
                            child: ElevatedButton(
                              onPressed: _loading ? null : _submit,
                              child: _loading
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: Color(0xFF4AE0FF),
                                      ),
                                    )
                                  : Text(
                                      _isRegister
                                          ? '[ CREATE ACCOUNT ]'
                                          : '[ AUTHENTICATE ]',
                                    ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 24),
                  Text(
                    'IRIS AI — ALL SYSTEMS NOMINAL',
                    style: GoogleFonts.spaceMono(
                      color: irisCyan.withOpacity(0.2),
                      fontSize: 8,
                      letterSpacing: 2,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
