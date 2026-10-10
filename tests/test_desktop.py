"""Synthetic native desktop flows; no panel, cloud request or real credentials."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import aim_control as control
import desktop_support as desktop
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QFontDatabase
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QMessageBox
from PySide6.QtTest import QTest
from desktop_window import MonitorWindow, ConfirmFlashDialog, ActionWorker


class DesktopSettingsTests(unittest.TestCase):
    def test_transient_windows_lock_keeps_atomic_config_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            control.save_config(dict(control.host.DEFAULT_CONFIG),root)
            replace=control.os.replace
            attempts=[]
            def transient(source,target):
                attempts.append(target)
                if len(attempts)==1:
                    error=PermissionError('synthetic sharing lock'); error.winerror=32
                    raise error
                return replace(source,target)
            with patch.object(control.os,'replace',side_effect=transient), patch.object(control.time,'sleep'):
                control.save_config(dict(control.host.DEFAULT_CONFIG,board='guition-p4',providers=['gemini']),root)
            self.assertEqual(control.local_config(root)['providers'],['gemini'])
            self.assertEqual(len(attempts),2)
            self.assertFalse(list((root/'tools').glob('*.tmp')))

    def test_preserves_existing_key_and_extra_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            control.save_config(dict(control.host.DEFAULT_CONFIG, board='guition-p4',
                                     providers=['zcode'], zai_key='fixture-private-key', custom=True), root)
            config = desktop.save_settings(root, 'waveshare-s3-43', ['gemini'], 'COM7', 60)
            self.assertEqual(config['zai_key'], 'fixture-private-key')
            self.assertTrue(config['custom'])
            self.assertEqual(config['board'], 'waveshare-s3-43')
            self.assertEqual(config['providers'], ['gemini'])
            self.assertEqual(desktop.save_settings(root, 'guition-p4', ['zcode'], 'auto', 240, clear_key=True)['zai_key'], '')

    def test_invalid_settings_never_replace_existing_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            control.save_config(dict(control.host.DEFAULT_CONFIG, board='guition-p4', providers=['gemini']), root)
            before = (root/'tools/aim_host.json').read_bytes()
            invalid = [('bad-board', ['gemini'], 'COM6', 60, ''),
                       ('guition-p4', [], 'COM6', 60, ''),
                       ('guition-p4', ['gemini'], 'https://attacker.invalid', 60, ''),
                       ('guition-p4', ['gemini'], 'COM6', True, ''),
                       ('guition-p4', ['gemini'], 'COM6', 60, 'secret\ninvalid')]
            for args in invalid:
                with self.assertRaises(ValueError): desktop.save_settings(root, *args)
                self.assertEqual((root/'tools/aim_host.json').read_bytes(), before)

    def test_log_is_bounded_and_redacts_keys_and_control_sequences(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'tools').mkdir()
            (root/'tools/aim_host.log').write_text('discard\n'*5000+'fixture-key\x1b[31m\nlast message\n')
            log=desktop.recent_log(root, ('fixture-key',))
            self.assertNotIn('fixture-key', log)
            self.assertNotIn('\x1b', log)
            self.assertIn('[REDACTED]', log)
            self.assertTrue(log.endswith('last message'))
            self.assertLessEqual(len(log.splitlines()), 100)

    def test_flash_revalidates_configuration_before_stopping_host(self):
        with patch.object(desktop, 'prepare_flash', return_value=('COM7', ['flasher'])), \
                patch.object(control, 'stop_host') as stop, patch.object(desktop.subprocess, 'Popen') as spawn:
            with self.assertRaises(control.SetupError):
                desktop.write_firmware(Path('.'), 'waveshare-s3-43', 'install', 'COM6', Mock())
        stop.assert_not_called(); spawn.assert_not_called()

    def test_console_host_is_owned_only_with_the_scoped_host_argument(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            ours=Mock(pid=123,info={'exe':str(root/'AI-Monitor-Console.exe'),'cmdline':['AI-Monitor-Console.exe','--host']})
            setup=Mock(pid=124,info={'exe':str(root/'AI-Monitor-Console.exe'),'cmdline':['AI-Monitor-Console.exe','--integrations']})
            other=Mock(pid=125,info={'exe':str(root/'other/AI-Monitor-Console.exe'),'cmdline':['AI-Monitor-Console.exe','--host']})
            with patch.object(control.psutil, 'process_iter', return_value=[ours,setup,other]):
                self.assertEqual(control.owned_hosts(root), [ours])


class DesktopWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])
        cls.application.setStyle('Fusion')
        if os.name == 'nt':
            for name in ('segoeui.ttf','segoeuib.ttf','consola.ttf'):
                QFontDatabase.addApplicationFont(str(Path(os.environ['SystemRoot'])/'Fonts'/name))

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.window = MonitorWindow(self.root, monitor=False)
        self.window.show()
        self.application.processEvents()
        self.addCleanup(self.window.close)
        self.addCleanup(self.window.deleteLater)

    def test_fresh_ui_has_no_selections_and_contains_nova(self):
        self.assertEqual(self.window.board.currentData(), '')
        self.assertFalse(any(box.isChecked() for box in self.window.providers.values()))
        self.assertFalse(self.window.nova.pixmap().isNull())
        self.assertFalse(self.window.windowIcon().isNull())
        self.assertTrue(self.window.activity.isReadOnly())
        self.assertTrue(self.window.host_log.isReadOnly())
        self.assertFalse((self.root/'tools/aim_host.json').exists())

    def test_s3_selection_and_save_use_real_widgets(self):
        self.window.board.setCurrentIndex(self.window.board.findData('waveshare-s3-43'))
        self.window.providers['gemini'].setChecked(True)
        self.window.port.setCurrentText('COM7')
        QTest.mouseClick(self.window.save_button, Qt.MouseButton.LeftButton)
        config=control.local_config(self.root)
        self.assertEqual(config['board'],'waveshare-s3-43')
        self.assertEqual(config['providers'],['gemini'])
        self.assertEqual(config['port'],'COM7')
        self.assertFalse(self.window.unsaved)
        self.assertIn('EXPERIMENTAL',self.window.board_help.text())

    def test_existing_key_is_not_loaded_into_the_visible_password_field(self):
        self.window.close()
        control.save_config(dict(control.host.DEFAULT_CONFIG,board='guition-p4',providers=['zcode'],zai_key='fixture-private-key'),self.root)
        window=MonitorWindow(self.root,monitor=False)
        self.addCleanup(window.close)
        self.assertEqual(window.key.text(),'')
        self.assertEqual(window.key.echoMode(),QLineEdit.EchoMode.Password)
        window.append_output('never expose fixture-private-key')
        self.assertNotIn('fixture-private-key',window.activity.toPlainText())

    def test_unsaved_selection_cannot_start_a_host(self):
        with patch.object(control,'start_host') as start, patch.object(QMessageBox,'warning'):
            self.window.start()
        start.assert_not_called()

    def test_flash_confirmation_requires_exact_text(self):
        dialog=ConfirmFlashDialog('waveshare-s3-43','COM7','install')
        self.addCleanup(dialog.deleteLater)
        self.assertFalse(dialog.write.isEnabled())
        dialog.confirm.setText('flash'); self.assertFalse(dialog.write.isEnabled())
        dialog.confirm.setText('FLASH'); self.assertTrue(dialog.write.isEnabled())

    def test_cancelled_firmware_leaves_host_and_usb_untouched(self):
        self.window.board.setCurrentIndex(self.window.board.findData('guition-p4'))
        self.window.providers['gemini'].setChecked(True)
        self.window.save()
        operation=Mock(); operation.exec.return_value=QDialog.DialogCode.Rejected
        with patch('desktop_window.FirmwareDialog',return_value=operation), \
                patch.object(desktop,'prepare_flash') as prepare, patch.object(control,'stop_host') as stop:
            self.window.flash()
        prepare.assert_not_called(); stop.assert_not_called()

    def test_closing_window_keeps_host_but_waits_for_running_actions(self):
        with patch.object(control,'stop_host') as stop:
            event=QCloseEvent(); self.window.closeEvent(event); self.assertTrue(event.isAccepted())
            self.window.busy=True
            event=QCloseEvent(); self.window.closeEvent(event); self.assertFalse(event.isAccepted())
            self.window.busy=False
        stop.assert_not_called()

    def test_worker_never_forwards_credential_exception_details(self):
        def fail(emit): raise ValueError('fixture-secret-key')
        worker=ActionWorker(fail,'Starting host'); result=[]
        worker.signals.finished.connect(lambda success,message: result.append((success,message)))
        worker.run()
        self.assertFalse(result[0][0])
        self.assertNotIn('fixture-secret-key',result[0][1])


if __name__ == '__main__': unittest.main()
