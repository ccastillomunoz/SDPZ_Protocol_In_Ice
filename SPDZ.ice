module SPDZ {
    interface Node {
        void sendShares(int shareValue, int shareMac);
        void computeSum();
        void revealSum();
        void receiveResult(int sum, int mac);
    };
};
