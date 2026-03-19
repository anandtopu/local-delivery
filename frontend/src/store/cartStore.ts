import { create } from "zustand";

interface Location {
  lat: number;
  lng: number;
}

interface CartState {
  items: Record<number, number>; // item_id → quantity
  location: Location | null;
  setLocation: (location: Location) => void;
  addItem: (itemId: number, quantity?: number) => void;
  removeItem: (itemId: number) => void;
  updateQuantity: (itemId: number, quantity: number) => void;
  clearCart: () => void;
}

export const useCartStore = create<CartState>((set) => ({
  items: {},
  location: null,

  setLocation: (location) => set({ location }),

  addItem: (itemId, quantity = 1) =>
    set((state) => ({
      items: {
        ...state.items,
        [itemId]: (state.items[itemId] ?? 0) + quantity,
      },
    })),

  removeItem: (itemId) =>
    set((state) => {
      const next = { ...state.items };
      delete next[itemId];
      return { items: next };
    }),

  updateQuantity: (itemId, quantity) =>
    set((state) => {
      if (quantity <= 0) {
        const next = { ...state.items };
        delete next[itemId];
        return { items: next };
      }
      return { items: { ...state.items, [itemId]: quantity } };
    }),

  clearCart: () => set({ items: {}, location: null }),
}));
