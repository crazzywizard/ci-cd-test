import React, { useEffect, useState } from "react";
import Avatar from "@material-ui/core/Avatar";
import StyledFirebaseAuth from "react-firebaseui/StyledFirebaseAuth";
import firebase, { generateUserDocument } from "../config/config";
import { auth, db } from "../config/config";
import CssBaseline from "@material-ui/core/CssBaseline";
import FormControlLabel from "@material-ui/core/FormControlLabel";
import Checkbox from "@material-ui/core/Checkbox";
import Link from "@material-ui/core/Link";
import Paper from "@material-ui/core/Paper";
import Box from "@material-ui/core/Box";
import Grid from "@material-ui/core/Grid";
import LockOutlinedIcon from "@material-ui/icons/LockOutlined";
import Typography from "@material-ui/core/Typography";
import FormGroup from "@material-ui/core/FormGroup";
import { makeStyles } from "@material-ui/core/styles";

const useStyles = makeStyles((theme) => ({
  root: {
    height: "100vh",
  },
  image: {
    backgroundImage: "url(img/background.jpg)",
    backgroundRepeat: "no-repeat",
    backgroundColor:
      theme.palette.type === "dark"
        ? theme.palette.grey[900]
        : theme.palette.grey[50],
    backgroundSize: "cover",
    backgroundPosition: "center",
    width: "100%",
    paddingTop: "40px",
    paddingBottom: "400px",
  },
  paper: {
    margin: theme.spacing(6, 6),
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  avatar: {
    margin: theme.spacing(1),
    backgroundColor: theme.palette.secondary.main,
  },
  form: {
    width: "100%", // Fix IE 11 issue.
    marginTop: theme.spacing(1),
  },
  submit: {
    margin: theme.spacing(3, 0, 2),
  },
}));
function Copyright() {
  return (
    <Typography variant="body2" color="textSecondary" align="center">
      {"Copyright © "}
      <Link color="inherit" href="https://voicefirsttech.com/">
        Voice First AI{" "}
      </Link>{" "}
      {new Date().getFullYear()}
      {"."}
    </Typography>
  );
}
function uuidv4() {
  return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, (c) =>
    (
      c ^
      (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))
    ).toString(16)
  );
}
export default function SignIn(props) {
  const classes = useStyles();
  const [userType, setUserType] = useState({
    parent: false,
    student: false,
  });
  const handleChange = (event) => {
    setUserType({ ...userType, [event.target.name]: event.target.checked });
  };
  let uiConfig = {
    signInFlow: "popup",
    signInOptions: [
      firebase.auth.GoogleAuthProvider.PROVIDER_ID,
      firebase.auth.EmailAuthProvider.PROVIDER_ID,
    ],
    callbacks: {
      signInSuccessWithAuthResult: function(authResult, redirectUrl) {
        return false;
      },
    },
  };
  useEffect(() => {
    auth.onAuthStateChanged(async (user) => {
      if (user) {
        const uid = user.uid;
        const code = uuidv4();
        const urlParams = new URLSearchParams(window.location.search);
        const state = urlParams.get("state");
        const redirectURI = urlParams.get("redirect_uri");
        const url = redirectURI + "?state=" + state + "&code=" + code;
        try {
          await db
            .collection("codes")
            .doc(uid)
            .set(
              {
                code: code,
                uid: uid,
                created_at: firebase.firestore.FieldValue.serverTimestamp(),
              },
              { merge: true }
            );
          await generateUserDocument(user, userType);
        } catch (error) {
          console.log(error);
        }

        // Redirect to url
        window.location.href = url;
      }
    });
  });
  return (
    <Grid container component="main" className={classes.root}>
      <CssBaseline />
      <Grid container justify="center" className={classes.image}>
        <Grid
          item
          xs={12}
          sm={8}
          md={5}
          component={Paper}
          direction="row"
          elevation={6}
          square
        >
          <Grid className={classes.paper}>
            <Avatar className={classes.avatar}>
              <LockOutlinedIcon />
            </Avatar>
            <Typography component="h1" variant="h5">
              Sign in
            </Typography>
            <Typography component="h1" variant="h5">
              Parent or Student?
            </Typography>
            <FormGroup row>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={userType.parent}
                    onChange={handleChange}
                    name="parent"
                    disabled={userType.student}
                  />
                }
                label="Parent"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={userType.student}
                    onChange={handleChange}
                    name="student"
                    disabled={userType.parent}
                  />
                }
                label="Student"
              />
            </FormGroup>

            <form className={classes.form} noValidate>
              {userType.student || userType.parent ? (
                <StyledFirebaseAuth
                  className={classes.form}
                  uiConfig={uiConfig}
                  firebaseAuth={auth}
                />
              ) : null}
              <Box mt={5}>
                <Copyright />
              </Box>
            </form>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  );
}
