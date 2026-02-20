@echo off
REM Seed dummy data using MySQL CLI
REM This bypasses Python SSL issues

echo ============================================================
echo SEEDING DUMMY DATA VIA MYSQL CLI
echo ============================================================
echo.
echo This will connect to your TiDB Cloud database and seed data.
echo You will be prompted for your password.
echo.
echo Database: loagma
echo Host: gateway01.ap-northeast-1.prod.aws.tidbcloud.com
echo.
pause

mysql -h gateway01.ap-northeast-1.prod.aws.tidbcloud.com ^
      -P 4000 ^
      -u 3JkMn3GrMm4dpze.root ^
      -p ^
      --ssl-mode=REQUIRED ^
      loagma ^
      < migrations\seed_dummy_data.sql

echo.
echo ============================================================
echo SEEDING COMPLETE!
echo ============================================================
pause
