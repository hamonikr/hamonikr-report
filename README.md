# HamoniKR Report

This is a troubleshooting tool to analyse crash reports and browse through important information.

## Build
Get source code
```
git clone https://github.com/hamonikr/hamonikrreport
cd hamonikrreport
```

Build
```
dpkg-buildpackage --no-sign
```

Install
```
cd ..
sudo dpkg -i hamonikrreport*.deb
```

## License
- Code: GPLv3
