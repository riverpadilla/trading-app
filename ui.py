"""Simple UI para interactuar con binance_test.py usando Tkinter"""
import tkinter as tk
from tkinter import messagebox
import binance_test

def consultar_saldos():
    """_summary_ Consulta y muestra los saldos de la cuenta."""
    saldos = binance_test.get_account_info()
    saldo_text.delete(1.0, tk.END)
    if "balances" in saldos:
        # Ordenar por nombre de moneda (asset)
        balances_ordenados = sorted(saldos["balances"], key=lambda x: x["asset"])
        for balance in balances_ordenados:
            asset = balance["asset"]
            free = balance["free"]
            locked = balance["locked"]
            saldo_text.insert(tk.END, f"{asset}: Disponible={free}, Bloqueado={locked}\n")
    else:
        saldo_text.insert(tk.END, str(saldos))

def depositar():
    """_summary_ Muestra información sobre el faucet."""
    messagebox.showinfo("Faucet", "Para incrementar saldos, usa el faucet:\nhttps://testnet.binance.vision/faucet")

def crear_orden():
    """_summary_ Crea una orden de compra/venta."""
    symbol = symbol_entry.get()
    side = side_var.get()
    quantity = float(quantity_entry.get())
    price = float(price_entry.get())
    orden = binance_test.create_order(symbol, side, quantity, price)
    orden_text.delete(1.0, tk.END)
    orden_text.insert(tk.END, str(orden))

def cancelar_orden():
    """_summary_ Cancela una orden existente."""
    symbol = symbol_entry.get()
    try:
        order_id = int(orderid_entry.get())
        cancel = binance_test.cancel_order(symbol, order_id)
        orden_text.delete(1.0, tk.END)
        orden_text.insert(tk.END, str(cancel))
    except ValueError:
        messagebox.showerror("Error", "Order ID debe ser un número entero.")

root = tk.Tk()
root.title("Binance Testnet UI")

tk.Label(root, text="Saldos:").grid(row=0, column=0, sticky="w")
saldo_text = tk.Text(root, height=8, width=60)
saldo_text.grid(row=1, column=0, columnspan=4)
tk.Button(root, text="Consultar Saldos", command=consultar_saldos).grid(row=2, column=0)

tk.Button(root, text="Depositar (Faucet)", command=depositar).grid(row=2, column=1)

tk.Label(root, text="Símbolo:").grid(row=3, column=0)
symbol_entry = tk.Entry(root)
symbol_entry.insert(0, "BTCUSDT")
symbol_entry.grid(row=3, column=1)

tk.Label(root, text="Lado:").grid(row=3, column=2)
side_var = tk.StringVar(value="BUY")
tk.OptionMenu(root, side_var, "BUY", "SELL").grid(row=3, column=3)

tk.Label(root, text="Cantidad:").grid(row=4, column=0)
quantity_entry = tk.Entry(root)
quantity_entry.insert(0, "0.001")
quantity_entry.grid(row=4, column=1)

tk.Label(root, text="Precio:").grid(row=4, column=2)
price_entry = tk.Entry(root)
price_entry.insert(0, "30000")
price_entry.grid(row=4, column=3)

tk.Button(root, text="Crear Orden", command=crear_orden).grid(row=5, column=0)

tk.Label(root, text="Order ID para cancelar:").grid(row=5, column=1)
orderid_entry = tk.Entry(root)
orderid_entry.grid(row=5, column=2)
tk.Button(root, text="Cancelar Orden", command=cancelar_orden).grid(row=5, column=3)

tk.Label(root, text="Resultado Orden:").grid(row=6, column=0, sticky="w")
orden_text = tk.Text(root, height=8, width=60)
orden_text.grid(row=7, column=0, columnspan=4)

root.mainloop()
