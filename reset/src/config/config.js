import firebase from "firebase/app";
import "firebase/firestore";
import "firebase/auth";
import "firebase/storage";

const config = {
  apiKey: "AIzaSyDstu_FrRzZY-3sKrPCH0qG92gd6yMp8aU",
  authDomain: "account-linking-testing.firebaseapp.com",
  projectId: "account-linking-testing",
  storageBucket: "account-linking-testing.appspot.com",
  messagingSenderId: "411913568054",
  appId: "1:411913568054:web:b7b1c3146bd3e68ac03d97",
  measurementId: "G-ETHT1TJMCL",
};

firebase.initializeApp(config);

export const db = firebase.firestore();
export const auth = firebase.auth();
export default firebase;
export const generateUserDocument = async (user, additionalData) => {
  if (!user) return;
  const userRef = db.doc(`Accounts/${user.uid}`);
  const snapshot = await userRef.get();
  if (!snapshot.exists) {
    const { email, displayName, photoURL } = user;
    try {
      await userRef.set({
        displayName,
        email,
        photoURL,
        ...additionalData,
      });
    } catch (error) {
      console.error("Error creating user document", error);
    }
  }
  return getUserDocument(user.uid);
};
const getUserDocument = async (uid) => {
  if (!uid) return null;
  try {
    const userDocument = await db.doc(`Accounts/${uid}`).get();
    return {
      uid,
      ...userDocument.data(),
    };
  } catch (error) {
    console.error("Error fetching user", error);
  }
};
