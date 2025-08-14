import os
import gettext
import gi
import subprocess

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from hamonikrreport import InfoReport, InfoReportAction

class Report(InfoReport):

    def __init__(self):

        gettext.install("hamonikr-report", "/usr/share/locale", names="ngettext")

        self.title = _("Security Status Check")
        self.icon = "security-medium-symbolic"
        self.has_ignore_button = True
        
        # 보안 점검 결과를 저장할 변수들
        self.security_issues = []
        self.security_warnings = []
        self.security_ok = []

    def is_pertinent(self):
        # 항상 보안 점검을 표시 (시스템 관리자가 정기적으로 확인할 수 있도록)
        return True

    def check_firewall_status(self):
        """방화벽 상태 점검"""
        try:
            result = subprocess.getoutput("ufw status")
            if "Status: active" in result:
                self.security_ok.append(_("Firewall is active"))
                return True
            elif "Status: inactive" in result:
                self.security_issues.append(_("Firewall is disabled"))
                return False
            else:
                self.security_warnings.append(_("Could not determine firewall status"))
                return None
        except:
            self.security_warnings.append(_("UFW firewall not installed"))
            return None

    def check_automatic_updates(self):
        """리눅스 민트 업데이트 매니저 설정 점검"""
        try:
            # 리눅스 민트의 업데이트 매니저 설정 확인
            config_file = "/home/{}/.config/mintupdate/mintupdate.conf".format(os.getenv('USER', 'user'))
            
            # mintupdate 패키지 설치 여부 확인
            result = subprocess.getoutput("dpkg-query -W --showformat='${db:Status-Status}' mintupdate 2>&1")
            if result == "installed":
                self.security_ok.append(_("Linux Mint Update Manager is installed"))
                
                # 자동 새로고침 설정 확인 (선택사항)
                if os.path.exists(config_file):
                    try:
                        with open(config_file, 'r') as f:
                            content = f.read()
                            if 'automatic_refresh=true' in content:
                                self.security_ok.append(_("Automatic update checking is enabled"))
                            else:
                                self.security_warnings.append(_("Consider enabling automatic update checking"))
                    except:
                        pass
                return True
            else:
                self.security_warnings.append(_("Linux Mint Update Manager not found"))
                return False
        except:
            self.security_warnings.append(_("Could not check update manager configuration"))
            return None

    def check_ssh_security(self):
        """SSH 서비스 보안 점검"""
        try:
            # SSH 서비스 실행 여부 확인
            ssh_running = subprocess.getoutput("systemctl is-active ssh") == "active"
            if not ssh_running:
                self.security_ok.append(_("SSH service is not running"))
                return True
            
            # SSH 설정 파일 점검
            ssh_config = "/etc/ssh/sshd_config"
            if os.path.exists(ssh_config):
                with open(ssh_config, 'r') as f:
                    content = f.read()
                    issues = []
                    if "PermitRootLogin yes" in content:
                        issues.append(_("SSH root login is enabled"))
                    if "PasswordAuthentication yes" in content and "PubkeyAuthentication no" in content:
                        issues.append(_("SSH password authentication is enabled without key authentication"))
                    
                    if issues:
                        self.security_issues.extend(issues)
                        return False
                    else:
                        self.security_ok.append(_("SSH service has secure configuration"))
                        return True
            else:
                self.security_warnings.append(_("SSH configuration file not found"))
                return None
        except:
            self.security_warnings.append(_("Could not check SSH security"))
            return None

    def check_sudo_users(self):
        """sudo 권한 사용자 점검"""
        try:
            result = subprocess.getoutput("getent group sudo")
            if result:
                users = result.split(':')[-1].strip()
                if users:
                    user_list = users.split(',')
                    if len(user_list) > 3:  # 일반적으로 3명 이상이면 많다고 판단
                        self.security_warnings.append(_("Multiple users have sudo privileges: %s") % users)
                    else:
                        self.security_ok.append(_("Sudo privileges are properly limited"))
                else:
                    self.security_warnings.append(_("No users have sudo privileges"))
            return True
        except:
            self.security_warnings.append(_("Could not check sudo users"))
            return None

    def check_security_packages(self):
        """보안 패키지 설치 상태 점검"""
        packages_to_check = {
            'ufw': _("Uncomplicated Firewall (UFW)"),
            'ahnlab-v3lite': _("AhnLab V3 Lite Antivirus"),
            'gufw': _("Firewall configuration tool"),
            'mintupdate': _("Linux Mint Update Manager")
        }
        
        missing_packages = []
        installed_packages = []
        
        for package, description in packages_to_check.items():
            try:
                result = subprocess.getoutput(f"dpkg-query -W --showformat='${{db:Status-Status}}' {package} 2>&1")
                if result == "installed":
                    installed_packages.append(description)
                else:
                    missing_packages.append(package)
            except:
                missing_packages.append(package)
        
        if installed_packages:
            self.security_ok.extend([_("Installed: %s") % pkg for pkg in installed_packages])
        
        if missing_packages:
            self.security_warnings.append(_("Security packages not installed: %s") % ", ".join(missing_packages))
        
        return len(missing_packages) == 0

    def check_file_permissions(self):
        """중요 시스템 파일 권한 점검"""
        critical_files = {
            '/etc/passwd': '644',
            '/etc/shadow': '640',
            '/etc/group': '644',
            '/etc/gshadow': '640'
        }
        
        permission_issues = []
        
        for file_path, expected_perm in critical_files.items():
            if os.path.exists(file_path):
                try:
                    stat_info = os.stat(file_path)
                    actual_perm = oct(stat_info.st_mode)[-3:]
                    if actual_perm != expected_perm:
                        permission_issues.append(f"{file_path}: {actual_perm} (expected {expected_perm})")
                except:
                    permission_issues.append(f"{file_path}: could not check permissions")
        
        if permission_issues:
            self.security_warnings.extend([_("File permission issue: %s") % issue for issue in permission_issues])
            return False
        else:
            self.security_ok.append(_("Critical system file permissions are correct"))
            return True

    def check_open_ports(self):
        """열린 포트 점검"""
        try:
            result = subprocess.getoutput("ss -tuln")
            lines = result.split('\n')[1:]  # 헤더 제거
            listening_ports = []
            
            for line in lines:
                if 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        local_addr = parts[4]
                        if ':' in local_addr:
                            port = local_addr.split(':')[-1]
                            if port not in ['22', '53']:  # SSH와 DNS는 일반적으로 허용
                                listening_ports.append(port)
            
            if listening_ports:
                unique_ports = list(set(listening_ports))
                if len(unique_ports) > 5:  # 5개 이상의 포트가 열려있으면 경고
                    self.security_warnings.append(_("Many network services are running (ports: %s)") % ", ".join(unique_ports[:10]))
                else:
                    self.security_ok.append(_("Network services are limited"))
            else:
                self.security_ok.append(_("No unnecessary network services detected"))
            
            return True
        except:
            self.security_warnings.append(_("Could not check open ports"))
            return None

    def get_descriptions(self):
        # 보안 점검 실행
        self.security_issues.clear()
        self.security_warnings.clear()
        self.security_ok.clear()
        
        self.check_firewall_status()
        self.check_automatic_updates()
        self.check_ssh_security()
        self.check_sudo_users()
        self.check_security_packages()
        self.check_file_permissions()
        self.check_open_ports()
        
        descriptions = []
        descriptions.append(_("System security status check completed."))
        descriptions.append("")
        
        if self.security_issues:
            descriptions.append(_("<b>⚠ Security Issues Found:</b>"))
            for issue in self.security_issues:
                descriptions.append(f"• {issue}")
            descriptions.append("")
        
        if self.security_warnings:
            descriptions.append(_("<b>⚠ Security Warnings:</b>"))
            for warning in self.security_warnings:
                descriptions.append(f"• {warning}")
            descriptions.append("")
        
        if self.security_ok:
            descriptions.append(_("<b>✓ Security Status OK:</b>"))
            for ok_item in self.security_ok:
                descriptions.append(f"• {ok_item}")
        
        return descriptions

    def get_actions(self):
        actions = []
        
        # 새로고침 액션
        action = InfoReportAction(label=_("Refresh Security Check"), callback=self.callback_refresh)
        actions.append(action)
        
        # 방화벽 활성화 액션 (방화벽이 비활성화된 경우)
        firewall_status = subprocess.getoutput("ufw status")
        if "Status: inactive" in firewall_status:
            action = InfoReportAction(label=_("Enable Firewall"), callback=self.callback_enable_firewall)
            action.set_style(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
            actions.append(action)
        
        # 보안 패키지 설치 액션
        action = InfoReportAction(label=_("Install Security Packages"), callback=self.callback_install_security_packages)
        actions.append(action)
        
        return actions

    def callback_refresh(self, data):
        # 새로고침 - 단순히 True를 반환하여 리로드 요청
        return True

    def callback_enable_firewall(self, data):
        try:
            # UFW 활성화
            subprocess.run(['pkexec', 'ufw', 'enable'], check=True)
            return True  # 성공시 리로드
        except subprocess.CalledProcessError:
            return False  # 실패시 리로드하지 않음
        except:
            return False

    def callback_install_security_packages(self, data):
        # 데스크톱 환경에 적합한 기본 보안 패키지들 설치
        packages = ['ufw', 'gufw']
        try:
            self.install_packages(packages)
            return True
        except:
            return False

if __name__ == "__main__":
    report = Report()
    print(report.is_pertinent())