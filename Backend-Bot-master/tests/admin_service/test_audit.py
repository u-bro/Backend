def test_audit_logger_logs_info(monkeypatch):
    # Ensure tests don't require Django to be installed: provide a minimal django.conf.settings
    import sys
    import types

    if 'django' not in sys.modules:
        django_mod = types.ModuleType('django')
        conf_mod = types.ModuleType('django.conf')
        # minimal settings object
        class _S: pass
        conf_mod.settings = _S()
        django_mod.conf = conf_mod
        sys.modules['django'] = django_mod
        sys.modules['django.conf'] = conf_mod

    calls = []

    def fake_info(msg):
        calls.append(msg)

    # patch logger.info used in audit module
    monkeypatch.setattr('admin_service.utils.audit.logger.info', fake_info)

    from admin_service.utils.audit import AuditLogger

    AuditLogger.log_action(
        admin_user_id=1,
        action='test_action',
        target_type='user',
        target_id=2,
        old_values={'a': 1},
        new_values={'a': 2},
        ip_address='127.0.0.1',
        user_agent='pytest'
    )

    assert any('Admin action' in c for c in calls)
