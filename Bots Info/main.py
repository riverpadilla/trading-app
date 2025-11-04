"""
Script de inicio rápido para el Bot de Trading
Permite elegir entre diferentes opciones de ejecución
"""

import os
import sys
import subprocess
import time

def print_menu():
    """Muestra el menú principal"""
    print("\n" + "="*60)
    print("🤖 BOT DE TRADING BNBUSDT - MENÚ PRINCIPAL")
    print("="*60)
    print("1. 📥 Descargar nuevos datos de Binance")
    print("2. 🖥️  Ejecutar bot (interfaz gráfica)")
    print("3. 💻 Ejecutar bot (línea de comandos)")
    print("4. 🧪 Verificar configuración del sistema")
    print("5. 📊 Ver archivos disponibles")
    print("6. 🔧 Información del sistema")
    print("7. 🚀 Abrir GUI directamente (método alternativo)")
    print("0. ❌ Salir")
    print("="*60)

def run_gui_alternative():
    """Método alternativo para ejecutar la GUI"""
    try:
        print("\n🚀 Método alternativo - Ejecutando interfaz gráfica")
        print("-" * 50)
        
        # Importar y ejecutar directamente
        import sys
        sys.path.append('.')
        
        # Ejecutar usando exec
        exec(open('trading_bot_gui.py').read())
        
    except Exception as e:
        print(f"❌ Error en método alternativo: {e}")
        print("\n💡 Intenta ejecutar manualmente:")
        print("   python trading_bot_gui.py")
        input("\nPresiona Enter para continuar...")

def list_files():
    """Lista archivos relevantes del proyecto"""
    print("\n📁 ARCHIVOS DEL PROYECTO:")
    print("-" * 40)
    
    # Buscar archivos CSV
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if csv_files:
        print("📊 Datos históricos:")
        for f in csv_files:
            size = os.path.getsize(f) / 1024 / 1024  # MB
            print(f"   • {f} ({size:.1f} MB)")
    else:
        print("📊 No hay archivos de datos (ejecuta opción 1)")
    
    # Buscar archivos de resultados
    result_files = [f for f in os.listdir('.') if f.startswith('backtest_results')]
    if result_files:
        print("\n📈 Resultados de backtesting:")
        for f in result_files:
            print(f"   • {f}")
    
    print()

def system_info():
    """Muestra información del sistema"""
    print("\n🔧 INFORMACIÓN DEL SISTEMA:")
    print("-" * 40)
    print(f"Python: {sys.version}")
    print(f"Directorio: {os.getcwd()}")
    
    # Verificar dependencias
    try:
        import pandas as pd
        print(f"✅ pandas: {pd.__version__}")
    except ImportError:
        print("❌ pandas: No instalado")
    
    try:
        from binance.client import Client
        print("✅ python-binance: Instalado")
    except ImportError:
        print("❌ python-binance: No instalado")
    
    try:
        import matplotlib
        print(f"✅ matplotlib: {matplotlib.__version__}")
    except ImportError:
        print("❌ matplotlib: No instalado")
    
    try:
        import numpy as np
        print(f"✅ numpy: {np.__version__}")
    except ImportError:
        print("❌ numpy: No instalado")
    
    print()

def run_command(command, description, is_gui=False):
    """Ejecuta un comando del sistema"""
    print(f"\n🚀 {description}")
    print("-" * len(description))
    
    # Determinar el comando Python correcto
    if os.path.exists('.venv/Scripts/python.exe'):
        python_cmd = '.venv/Scripts/python.exe'
    else:
        python_cmd = 'python'
    
    full_command = [python_cmd, command]
    print(f"Ejecutando: {' '.join(full_command)}")
    
    try:
        if is_gui:
            # Para interfaces gráficas, usar subprocess sin esperar
            process = subprocess.Popen(full_command, 
                                     creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            print(f"✅ {description} iniciado (PID: {process.pid})")
            print("💡 La aplicación se abrió en una ventana separada")
        else:
            # Para comandos de consola, esperar a que terminen
            result = subprocess.run(full_command, capture_output=False, text=True)
            if result.returncode == 0:
                print(f"✅ {description} completado exitosamente")
            else:
                print(f"❌ Error en {description} (código: {result.returncode})")
    
    except FileNotFoundError:
        print(f"❌ Error: No se pudo encontrar {python_cmd}")
        print("💡 Asegúrate de que Python esté instalado y configurado")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    
    if not is_gui:
        input("\nPresiona Enter para continuar...")

def main():
    """Función principal del menú"""
    
    while True:
        print_menu()
        
        try:
            choice = input("Selecciona una opción (0-7): ").strip()
            
            if choice == '0':
                print("\n👋 ¡Hasta luego!")
                break
            
            elif choice == '1':
                run_command('binance_downloader.py', 
                           'Descargando datos de Binance')
            
            elif choice == '2':
                run_command('trading_bot_gui.py', 
                           'Ejecutando interfaz gráfica', is_gui=True)
                input("\nPresiona Enter para continuar...")
            
            elif choice == '3':
                run_command('trading_bot.py', 
                           'Ejecutando bot en línea de comandos')
            
            elif choice == '4':
                run_command('test_setup.py', 
                           'Verificando configuración')
            
            elif choice == '5':
                list_files()
                input("Presiona Enter para continuar...")
            
            elif choice == '6':
                system_info()
                input("Presiona Enter para continuar...")
            
            elif choice == '7':
                run_gui_alternative()
            
            else:
                print("❌ Opción no válida. Intenta de nuevo.")
                input("Presiona Enter para continuar...")
        
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("Presiona Enter para continuar...")

if __name__ == "__main__":
    main()