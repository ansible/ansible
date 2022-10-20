package com.example.cociricullar

import android.os.Bundle
import android.os.Parcel
import android.os.Parcelable
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
//import androidx.compose.foundation.gestures
//import androidx.compose.foundation.gestures.ModifierLocalScrollableContainerProvider.value
import androidx.compose.foundation.layout.*
import androidx.compose.material.Button
import androidx.compose.material.MaterialTheme
import androidx.compose.material.Surface
import androidx.compose.material.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.example.cociricullar.ui.theme.COCIRICULLARTheme
import androidx.compose.ui.Modifier as Modifier1

class MainActivity() : ComponentActivity(), Parcelable {
    constructor(parcel: Parcel) : this() {
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            COCIRICULLARTheme {
                // A surface container using the 'background' color from the theme
                Surface(
                    modifier = Modifier1.fillMaxSize(),
                    color = MaterialTheme.colors.background
                ) {
                    LoginButton(
                        Modifier1
                            .fillMaxSize()
                            .wrapContentSize(Alignment.Center)
                    )

                }
            }
        }
    }

    override fun writeToParcel(parcel: Parcel, flags: Int) {

    }

    override fun describeContents(): Int {
        return 0
    }

    companion object CREATOR : Parcelable.Creator<MainActivity> {
        override fun createFromParcel(parcel: Parcel): MainActivity {
            return MainActivity(parcel)
        }

        override fun newArray(size: Int): Array<MainActivity?> {
            return arrayOfNulls(size)
        }
    }
}

@Preview
@Composable
fun DiceRoller(){
    LoginButton(modifier = Modifier1
        .fillMaxSize()
        .wrapContentSize(Alignment.Center))
}

@Composable
fun DiceWithButtonAndImage(modifier: Modifier1 = Modifier1){

    var result by remember {
         mutableStateOf( 1)
    }
    val imageResource = when(result){
        1 -> R.drawable.virat
        2 -> R.drawable.rohit
        3 -> R.drawable.rahul
        4 -> R.drawable.pandya
        5 -> R.drawable.bumrah
        else -> R.drawable.dice_6
    }



    Column(
        modifier = Modifier1,
        horizontalAlignment = Alignment.CenterHorizontally) {

        Image(
            painter = painterResource(imageResource),
            contentDescription = result.toString())
            Spacer(modifier = Modifier1.height(16.dp))
            Button(onClick = { result = (1..6 ).random() }) {
            Text(text = "Login")


        }
    }

}

